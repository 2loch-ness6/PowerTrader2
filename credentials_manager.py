"""
Secure credential management for PowerTrader2.
Uses OS-level keyring for secure storage of API credentials.
"""

import keyring
import logging
from typing import Optional, Tuple


class CredentialsManager:
    """Manages secure storage and retrieval of API credentials using OS keyring."""
    
    SERVICE_NAME = "PowerTrader2"
    KEY_USERNAME = "robinhood_api_key"
    SECRET_USERNAME = "robinhood_api_secret"
    
    def __init__(self):
        """Initialize the credentials manager."""
        self.logger = logging.getLogger(__name__)
    
    def store_api_key(self, key: str, secret: str) -> None:
        """
        Store encrypted API credentials in OS keyring.
        
        Args:
            key: The API key (public key)
            secret: The API secret (private key)
            
        Raises:
            Exception: If credentials cannot be stored
        """
        try:
            keyring.set_password(self.SERVICE_NAME, self.KEY_USERNAME, key)
            keyring.set_password(self.SERVICE_NAME, self.SECRET_USERNAME, secret)
            self.logger.info("API credentials stored successfully in keyring")
        except Exception as e:
            self.logger.error(f"Failed to store credentials in keyring: {e}")
            raise
    
    def retrieve_api_key(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Retrieve and decrypt API credentials from OS keyring.
        
        Returns:
            Tuple of (api_key, api_secret), or (None, None) if not found
        """
        try:
            key = keyring.get_password(self.SERVICE_NAME, self.KEY_USERNAME)
            secret = keyring.get_password(self.SERVICE_NAME, self.SECRET_USERNAME)
            
            if key and secret:
                self.logger.debug("API credentials retrieved from keyring")
                return (key, secret)
            else:
                self.logger.warning("API credentials not found in keyring")
                return (None, None)
        except Exception as e:
            self.logger.error(f"Failed to retrieve credentials from keyring: {e}")
            return (None, None)
    
    def delete_api_key(self) -> None:
        """
        Delete API credentials from OS keyring.
        
        Raises:
            Exception: If credentials cannot be deleted
        """
        try:
            keyring.delete_password(self.SERVICE_NAME, self.KEY_USERNAME)
            keyring.delete_password(self.SERVICE_NAME, self.SECRET_USERNAME)
            self.logger.info("API credentials deleted from keyring")
        except keyring.errors.PasswordDeleteError:
            self.logger.warning("No credentials found to delete")
        except Exception as e:
            self.logger.error(f"Failed to delete credentials from keyring: {e}")
            raise
    
    def has_credentials(self) -> bool:
        """
        Check if credentials exist in keyring.
        
        Returns:
            True if credentials exist, False otherwise
        """
        key, secret = self.retrieve_api_key()
        return key is not None and secret is not None
