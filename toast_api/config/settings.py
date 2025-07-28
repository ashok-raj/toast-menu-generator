"""Configuration management for Toast API client."""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ToastConfig:
    """Configuration class for Toast API settings."""
    
    def __init__(self):
        self.hostname = self._get_required_env('TOAST_HOSTNAME')
        self.client_id = self._get_required_env('TOAST_CLIENT_ID')
        self.client_secret = self._get_required_env('TOAST_CLIENT_SECRET')
        self.restaurant_guid = self._get_required_env('TOAST_RESTAURANT_GUID')
        
        # Cache settings
        self.token_cache_file = os.getenv('TOKEN_CACHE_FILE', 'token_cache.json')
        self.menu_cache_file = os.getenv('MENU_CACHE_FILE', 'menu_v2_out.json')
        
        # API settings
        self.api_timeout = int(os.getenv('API_TIMEOUT', '30'))
        
        # Restaurant info for menu generation
        self.restaurant_name = os.getenv('RESTAURANT_NAME', 'Restaurant')
        self.restaurant_address = os.getenv('RESTAURANT_ADDRESS', '')
        self.restaurant_phone = os.getenv('RESTAURANT_PHONE', '')
        self.restaurant_website = os.getenv('RESTAURANT_WEBSITE', '')
        
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable '{key}' not found")
        return value
    
    @property
    def auth_url(self) -> str:
        """Get authentication URL."""
        return f"{self.hostname}/authentication/v1/authentication/login"
    
    @property
    def menus_url(self) -> str:
        """Get menus API URL."""
        return f"{self.hostname}/menus/v2/menus"
    
    def get_auth_headers(self, token: str) -> dict:
        """Get headers for authenticated requests."""
        return {
            "Authorization": f"Bearer {token}",
            "Toast-Restaurant-External-Id": self.restaurant_guid,
            "Content-Type": "application/json"
        }

# Global config instance
config = ToastConfig()
