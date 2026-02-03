"""
API rate limiter with exponential backoff for PowerTrader2.
Prevents API rate limit violations and handles 429 errors gracefully.
"""

import time
import logging
from collections import deque
from typing import Callable, Any, Optional, Dict
from functools import wraps


class RateLimiter:
    """Rate limiter with exponential backoff for API calls."""
    
    def __init__(self, max_calls: int = 60, period: int = 60):
        """
        Initialize the rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed per period
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
        self.logger = logging.getLogger(__name__)
        self.paused_until = 0  # Timestamp when trading pause ends
    
    def wait_if_needed(self) -> None:
        """Block until rate limit allows next call."""
        now = time.time()
        
        # Check if we're in a pause period
        if now < self.paused_until:
            wait_time = self.paused_until - now
            self.logger.warning(f"Trading paused, waiting {wait_time:.1f}s")
            time.sleep(wait_time)
            return
        
        # Remove calls outside the current window
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()
        
        # If we're at the limit, wait until the oldest call expires
        if len(self.calls) >= self.max_calls:
            sleep_time = self.calls[0] + self.period - now
            if sleep_time > 0:
                self.logger.debug(f"Rate limit reached, sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
                # Clean up expired calls after sleeping
                while self.calls and self.calls[0] < time.time() - self.period:
                    self.calls.popleft()
    
    def record_call(self) -> None:
        """Record a call to the rate-limited resource."""
        self.calls.append(time.time())
    
    def execute_with_backoff(
        self,
        func: Callable,
        *args,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 16.0,
        **kwargs
    ) -> Any:
        """
        Execute function with exponential backoff on 429 errors.
        
        Args:
            func: Function to call
            *args: Positional arguments for func
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds for exponential backoff
            max_delay: Maximum delay in seconds between retries
            **kwargs: Keyword arguments for func
            
        Returns:
            Result of func(*args, **kwargs)
            
        Raises:
            Exception: If all retries fail
        """
        retry_count = 0
        delay = initial_delay
        
        while retry_count <= max_retries:
            # Wait if rate limit requires it
            self.wait_if_needed()
            
            try:
                # Record this call
                self.record_call()
                
                # Execute the function
                result = func(*args, **kwargs)
                
                # Check if result is a response object with status code
                if hasattr(result, 'status_code'):
                    if result.status_code == 429:
                        # Parse Retry-After header if present
                        retry_after = result.headers.get('Retry-After')
                        if retry_after:
                            try:
                                delay = float(retry_after)
                                self.logger.warning(f"HTTP 429: Rate limited, Retry-After: {delay}s")
                            except ValueError:
                                self.logger.warning(f"HTTP 429: Rate limited, using exponential backoff")
                        else:
                            self.logger.warning(f"HTTP 429: Rate limited, delay: {delay}s")
                        
                        if retry_count >= max_retries:
                            self.logger.error(f"Max retries ({max_retries}) reached, pausing trading for 5 minutes")
                            self.paused_until = time.time() + 300  # Pause for 5 minutes
                            raise Exception(f"Rate limit exceeded after {max_retries} retries")
                        
                        time.sleep(delay)
                        delay = min(delay * 2, max_delay)
                        retry_count += 1
                        continue
                
                # Success - return result
                return result
                
            except Exception as e:
                # Check if it's a rate limit error in the exception
                if '429' in str(e) or 'rate limit' in str(e).lower():
                    self.logger.warning(f"Rate limit error: {e}")
                    
                    if retry_count >= max_retries:
                        self.logger.error(f"Max retries ({max_retries}) reached, pausing trading for 5 minutes")
                        self.paused_until = time.time() + 300  # Pause for 5 minutes
                        raise
                    
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)
                    retry_count += 1
                    continue
                
                # Not a rate limit error - re-raise immediately
                raise
        
        # Should never reach here, but just in case
        raise Exception(f"Failed to execute after {max_retries} retries")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current rate limiter statistics.
        
        Returns:
            Dictionary with rate limiter stats
        """
        now = time.time()
        # Count calls in current window
        recent_calls = sum(1 for call_time in self.calls if call_time > now - self.period)
        
        return {
            "calls_in_window": recent_calls,
            "max_calls": self.max_calls,
            "period_seconds": self.period,
            "is_paused": now < self.paused_until,
            "pause_remaining_seconds": max(0, self.paused_until - now) if now < self.paused_until else 0,
        }


def rate_limited(max_calls: int = 60, period: int = 60):
    """
    Decorator to add rate limiting to a function.
    
    Args:
        max_calls: Maximum number of calls allowed per period
        period: Time period in seconds
        
    Example:
        @rate_limited(max_calls=60, period=60)
        def api_call():
            return requests.get(url)
    """
    limiter = RateLimiter(max_calls=max_calls, period=period)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return limiter.execute_with_backoff(func, *args, **kwargs)
        return wrapper
    
    return decorator
