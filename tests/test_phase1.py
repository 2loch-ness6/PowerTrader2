"""
Unit tests for Phase 1 security and reliability modules.
"""

import os
import sys
import json
import time
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import Mock, patch, MagicMock

from credentials_manager import CredentialsManager
from api_rate_limiter import RateLimiter
from integrity_checker import IntegrityChecker, IntegrityError
from safe_file_io import atomic_write_json, atomic_read_json, append_jsonl


class TestCredentialsManager:
    """Tests for secure credential storage."""
    
    def test_store_and_retrieve_credentials(self):
        """Verify credentials can be stored and retrieved."""
        manager = CredentialsManager()
        test_key = "test_api_key_12345"
        test_secret = "test_secret_67890"
        
        # Store credentials
        manager.store_api_key(test_key, test_secret)
        
        # Retrieve credentials
        retrieved_key, retrieved_secret = manager.retrieve_api_key()
        
        assert retrieved_key == test_key
        assert retrieved_secret == test_secret
        
        # Cleanup
        manager.delete_api_key()
    
    def test_retrieve_nonexistent_credentials(self):
        """Verify retrieving non-existent credentials returns None."""
        manager = CredentialsManager()
        
        # Ensure no credentials exist
        try:
            manager.delete_api_key()
        except:
            pass
        
        # Try to retrieve
        key, secret = manager.retrieve_api_key()
        
        assert key is None
        assert secret is None
    
    def test_has_credentials(self):
        """Verify has_credentials correctly detects presence."""
        manager = CredentialsManager()
        
        # Store credentials
        manager.store_api_key("test_key", "test_secret")
        assert manager.has_credentials() is True
        
        # Delete credentials
        manager.delete_api_key()
        assert manager.has_credentials() is False


class TestRateLimiter:
    """Tests for API rate limiting."""
    
    def test_rate_limiter_basic(self):
        """Verify rate limiter blocks after max_calls."""
        limiter = RateLimiter(max_calls=5, period=2)
        
        # Make 5 calls quickly
        for _ in range(5):
            limiter.record_call()
        
        # Next call should require waiting
        stats = limiter.get_stats()
        assert stats["calls_in_window"] == 5
        assert stats["max_calls"] == 5
    
    def test_rate_limiter_window_expiry(self):
        """Verify rate limiter window expires correctly."""
        limiter = RateLimiter(max_calls=3, period=1)
        
        # Make 3 calls
        for _ in range(3):
            limiter.record_call()
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Calls should have expired
        stats = limiter.get_stats()
        assert stats["calls_in_window"] == 0
    
    def test_execute_with_backoff_success(self):
        """Verify successful function execution."""
        limiter = RateLimiter(max_calls=10, period=60)
        
        def test_func(x, y):
            return x + y
        
        result = limiter.execute_with_backoff(test_func, 2, 3)
        assert result == 5
    
    def test_execute_with_backoff_429_retry(self):
        """Verify 429 error triggers retry."""
        limiter = RateLimiter(max_calls=10, period=60)
        
        # Mock function that fails first, then succeeds
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {}
        
        call_count = [0]
        
        def test_func():
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_response
            return Mock(status_code=200)
        
        result = limiter.execute_with_backoff(test_func, max_retries=3, initial_delay=0.1)
        assert call_count[0] == 2  # Failed once, succeeded on retry


class TestIntegrityChecker:
    """Tests for file integrity checking."""
    
    def setup_method(self):
        """Create temporary directory for tests."""
        self.test_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_generate_checksums(self):
        """Verify checksum generation for files."""
        checker = IntegrityChecker()
        
        # Create test files
        test_file1 = Path(self.test_dir) / "model1.json"
        test_file2 = Path(self.test_dir) / "model2.json"
        test_file1.write_text('{"test": "data1"}')
        test_file2.write_text('{"test": "data2"}')
        
        # Generate checksums
        checksums = checker.generate_checksums(self.test_dir)
        
        assert len(checksums) == 2
        assert "model1.json" in checksums
        assert "model2.json" in checksums
        assert len(checksums["model1.json"]) == 64  # SHA-256 hex length
    
    def test_verify_integrity_success(self):
        """Verify integrity check passes for unmodified files."""
        checker = IntegrityChecker()
        
        # Create test file
        test_file = Path(self.test_dir) / "model.json"
        test_file.write_text('{"test": "data"}')
        
        # Generate and save checksums
        checksums = checker.generate_checksums(self.test_dir)
        checker.save_checksums(self.test_dir, checksums)
        
        # Verify integrity (should pass)
        assert checker.verify_integrity(self.test_dir) is True
    
    def test_verify_integrity_failure(self):
        """Verify integrity check fails for modified files."""
        checker = IntegrityChecker()
        
        # Create test file
        test_file = Path(self.test_dir) / "model.json"
        test_file.write_text('{"test": "data"}')
        
        # Generate and save checksums
        checksums = checker.generate_checksums(self.test_dir)
        checker.save_checksums(self.test_dir, checksums)
        
        # Modify the file
        test_file.write_text('{"test": "modified"}')
        
        # Verify integrity (should fail)
        with pytest.raises(IntegrityError):
            checker.verify_integrity(self.test_dir)
    
    def test_update_checksums(self):
        """Verify checksum update after file modification."""
        checker = IntegrityChecker()
        
        # Create test file
        test_file = Path(self.test_dir) / "model.json"
        test_file.write_text('{"test": "data"}')
        
        # Generate initial checksums
        checker.update_checksums(self.test_dir)
        original_checksums = checker.load_checksums(self.test_dir)
        
        # Modify file
        test_file.write_text('{"test": "modified"}')
        
        # Update checksums
        checker.update_checksums(self.test_dir)
        new_checksums = checker.load_checksums(self.test_dir)
        
        # Checksums should be different
        assert original_checksums["model.json"] != new_checksums["model.json"]


class TestSafeFileIO:
    """Tests for safe file I/O operations."""
    
    def setup_method(self):
        """Create temporary directory for tests."""
        self.test_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_atomic_write_json(self):
        """Verify atomic JSON write."""
        test_file = os.path.join(self.test_dir, "test.json")
        test_data = {"key": "value", "number": 42}
        
        # Write data
        atomic_write_json(test_file, test_data)
        
        # Read and verify
        with open(test_file, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == test_data
    
    def test_atomic_read_json(self):
        """Verify atomic JSON read."""
        test_file = os.path.join(self.test_dir, "test.json")
        test_data = {"key": "value", "number": 42}
        
        # Write data directly
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Read with atomic_read_json
        loaded_data = atomic_read_json(test_file)
        
        assert loaded_data == test_data
    
    def test_atomic_read_nonexistent(self):
        """Verify reading non-existent file raises error."""
        test_file = os.path.join(self.test_dir, "nonexistent.json")
        
        with pytest.raises(FileNotFoundError):
            atomic_read_json(test_file)
    
    def test_append_jsonl(self):
        """Verify JSONL append operation."""
        test_file = os.path.join(self.test_dir, "test.jsonl")
        
        # Append multiple objects
        obj1 = {"id": 1, "value": "first"}
        obj2 = {"id": 2, "value": "second"}
        obj3 = {"id": 3, "value": "third"}
        
        append_jsonl(test_file, obj1)
        append_jsonl(test_file, obj2)
        append_jsonl(test_file, obj3)
        
        # Read and verify
        with open(test_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 3
        assert json.loads(lines[0]) == obj1
        assert json.loads(lines[1]) == obj2
        assert json.loads(lines[2]) == obj3
    
    def test_atomic_write_overwrites_existing(self):
        """Verify atomic write correctly overwrites existing file."""
        test_file = os.path.join(self.test_dir, "test.json")
        
        # Write initial data
        initial_data = {"version": 1}
        atomic_write_json(test_file, initial_data)
        
        # Overwrite with new data
        new_data = {"version": 2, "updated": True}
        atomic_write_json(test_file, new_data)
        
        # Verify new data
        loaded_data = atomic_read_json(test_file)
        assert loaded_data == new_data
        assert "version" in loaded_data
        assert loaded_data["version"] == 2


def test_import_modules():
    """Verify all new modules can be imported."""
    import credentials_manager
    import api_rate_limiter
    import integrity_checker
    import safe_file_io
    import migrate_credentials
    
    assert hasattr(credentials_manager, 'CredentialsManager')
    assert hasattr(api_rate_limiter, 'RateLimiter')
    assert hasattr(integrity_checker, 'IntegrityChecker')
    assert hasattr(safe_file_io, 'atomic_write_json')


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
