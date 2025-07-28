"""Authentication handling for Toast API."""
import requests
from datetime import datetime, timedelta
from typing import Tuple
from ..config.settings import config
from ..client.exceptions import AuthenticationError
from ..utils.cache import TokenCache
from ..utils.logger import logger

class ToastAuthenticator:
    """Handle Toast API authentication."""
    
    def __init__(self):
        self.token_cache = TokenCache(config.token_cache_file)
    
    def get_valid_token(self) -> Tuple[str, datetime]:
        """Get a valid access token, refreshing if necessary."""
        # Try to load from cache first
        cached_token, expiry = self.token_cache.load_token()
        if cached_token and expiry:
            return cached_token, expiry
        
        # Refresh token from API
        return self._refresh_token()
    
    def _refresh_token(self) -> Tuple[str, datetime]:
        """Refresh token from Toast API."""
        logger.info("🔐 Refreshing token from API")
        
        payload = {
            "clientId": config.client_id,
            "clientSecret": config.client_secret,
            "userAccessType": "TOAST_MACHINE_CLIENT"
        }
        
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(
                config.auth_url,
                json=payload,
                headers=headers,
                timeout=config.api_timeout
            )
            
            if response.status_code == 200:
                token_data = response.json()["token"]
                access_token = token_data["accessToken"]
                expires_in = token_data["expiresIn"]
                
                # Calculate expiry time
                expiry = datetime.now() + timedelta(seconds=expires_in)
                
                # Cache the token
                self.token_cache.save_token(access_token, expiry)
                
                logger.info("✅ Token refreshed successfully")
                return access_token, expiry
                
            else:
                raise AuthenticationError(
                    f"Authentication failed with status {response.status_code}: {response.text}"
                )
                
        except requests.RequestException as e:
            raise AuthenticationError(f"Network error during authentication: {e}")
