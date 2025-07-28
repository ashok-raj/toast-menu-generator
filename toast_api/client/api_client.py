"""Main Toast API client."""
import requests
from typing import Dict, Any, Optional
from ..config.settings import config
from ..client.auth import ToastAuthenticator
from ..client.exceptions import APIRequestError
from ..utils.logger import logger

class ToastAPIClient:
    """Main client for Toast API operations."""
    
    def __init__(self):
        self.authenticator = ToastAuthenticator()
        self._current_token = None
        self._token_expiry = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with valid token."""
        # Get fresh token if needed
        token, expiry = self.authenticator.get_valid_token()
        self._current_token = token
        self._token_expiry = expiry
        
        return config.get_auth_headers(token)
    
    def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated API request with error handling."""
        headers = self._get_headers()
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=config.api_timeout,
                **kwargs
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise APIRequestError(
                    f"API request failed with status {response.status_code}",
                    status_code=response.status_code,
                    response_text=response.text
                )
                
        except requests.RequestException as e:
            raise APIRequestError(f"Network error during API request: {e}")
    
    def get_menus(self) -> Dict[str, Any]:
        """Fetch menu data from Toast API."""
        logger.info("📡 Fetching menu data from API")
        
        data = self._make_request('GET', config.menus_url)
        
        logger.info("✅ Menu data fetched successfully")
        return data
    
    def get_menu_groups(self) -> list:
        """Get all menu group names."""
        menu_data = self.get_menus()
        
        group_names = set()
        for menu in menu_data.get("menus", []):
            for group in menu.get("menuGroups", []):
                name = group.get("name")
                if name:
                    group_names.add(name)
        
        return sorted(group_names)
    
    def get_menu_items_by_group(self, group_name: str, include_3pd: bool = False) -> list:
        """Get menu items for a specific group."""
        menu_data = self.get_menus()
        items = []
        
        for menu in menu_data.get("menus", []):
            menu_name = menu.get("name", "").lower()
            has_3pd = "3pd" in menu_name
            
            # Filter based on 3pd preference
            if include_3pd and not has_3pd:
                continue
            if not include_3pd and has_3pd:
                continue
            
            # Skip certain menu types
            if any(term in menu_name for term in ["owner", "otter", "happy", "beer", "catering", "weekend"]):
                continue
            
            for group in menu.get("menuGroups", []):
                if group.get("name") == group_name:
                    visibility = group.get("visibility", [])
                    
                    # Check visibility for 3pd
                    if include_3pd and "ORDERING_PARTNERS" not in visibility:
                        continue
                    
                    for item in group.get("menuItems", []):
                        item_name = item.get("name", "")
                        price = item.get("price")
                        formatted_price = f"${price:.2f}" if price is not None else ""
                        
                        items.append({
                            "name": item_name,
                            "price": price,
                            "formatted_price": formatted_price,
                            "menu": menu.get("name", ""),
                            "group": group_name
                        })
        
        return items
