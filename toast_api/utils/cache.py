"""Caching utilities for Toast API client."""
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple, Any
from ..client.exceptions import CacheError
from ..utils.logger import logger

class TokenCache:
    """Handle token caching operations."""
    
    def __init__(self, cache_file: str = 'token_cache.json'):
        self.cache_file = cache_file
    
    def load_token(self) -> Tuple[Optional[str], Optional[datetime]]:
        """Load cached token if valid."""
        try:
            if not os.path.exists(self.cache_file):
                return None, None
            
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                
            expiry = datetime.fromisoformat(data['expiryTime'])
            
            # Check if token is still valid (with 5 minute buffer)
            if expiry > datetime.now() + timedelta(minutes=5):
                logger.info("🔄 Using cached token")
                return data['accessToken'], expiry
            else:
                logger.info("⏰ Cached token expired")
                return None, None
                
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Error loading cached token: {e}")
            return None, None
    
    def save_token(self, token: str, expiry: datetime) -> None:
        """Save token to cache."""
        try:
            cache_data = {
                "accessToken": token,
                "expiryTime": expiry.isoformat()
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.info("💾 Token cached successfully")
            
        except (IOError, json.JSONEncodeError) as e:
            raise CacheError(f"Failed to save token cache: {e}")

class DataCache:
    """Handle general data caching operations."""
    
    def __init__(self, cache_file: str):
        self.cache_file = cache_file
    
    def load_data(self) -> Optional[dict]:
        """Load cached data if exists."""
        try:
            if not os.path.exists(self.cache_file):
                return None
            
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                
            logger.info(f"📁 Using cached data from {self.cache_file}")
            return data
            
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading cached data: {e}")
            return None
    
    def save_data(self, data: dict) -> None:
        """Save data to cache."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"💾 Data cached to {self.cache_file}")
            
        except (IOError, json.JSONEncodeError) as e:
            raise CacheError(f"Failed to save data cache: {e}")
    
    def clear_cache(self) -> None:
        """Clear cached data."""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                logger.info(f"🗑️ Cleared cache {self.cache_file}")
        except IOError as e:
            logger.warning(f"Error clearing cache: {e}")
