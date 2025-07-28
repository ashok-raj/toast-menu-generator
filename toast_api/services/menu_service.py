"""Menu-related business logic and operations."""
from typing import Dict, List, Any, Optional
from ..client.api_client import ToastAPIClient
from ..utils.cache import DataCache
from ..config.settings import config
from ..utils.logger import logger
from ..models.menu import Menu, MenuGroup, MenuItem

class MenuService:
    """Service for menu operations."""
    
    def __init__(self, use_cache: bool = True):
        self.api_client = ToastAPIClient()
        self.use_cache = use_cache
        self.data_cache = DataCache(config.menu_cache_file) if use_cache else None
    
    def get_menu_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get menu data, using cache if available."""
        if not force_refresh and self.use_cache:
            cached_data = self.data_cache.load_data()
            if cached_data:
                return cached_data
        
        # Fetch fresh data from API
        logger.info("📡 Fetching fresh menu data from API")
        data = self.api_client.get_menus()
        
        # Cache the data
        if self.use_cache:
            self.data_cache.save_data(data)
        
        return data
    
    def get_all_menu_groups(self, force_refresh: bool = False) -> List[str]:
        """Get all available menu group names."""
        data = self.get_menu_data(force_refresh)
        
        group_names = set()
        for menu in data.get("menus", []):
            for group in menu.get("menuGroups", []):
                name = group.get("name")
                if name:
                    group_names.add(name)
        
        return sorted(group_names)
    
    def get_grouped_menu_items(self, 
                             group_order: List[str], 
                             include_3pd: bool = False,
                             include_prices: bool = False,
                             force_refresh: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """Get menu items organized by groups."""
        data = self.get_menu_data(force_refresh)
        grouped_items = {}
        
        for menu in data.get("menus", []):
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
                group_name = group.get("name", "")
                if group_name not in group_order:
                    continue
                
                visibility = group.get("visibility", [])
                if include_3pd and "ORDERING_PARTNERS" not in visibility:
                    continue
                
                for item in group.get("menuItems", []):
                    item_name = item.get("name", "")
                    price = item.get("price")
                    formatted_price = f"${price:.2f}" if price is not None else ""
                    
                    item_data = {
                        "name": item_name,
                        "formatted_price": formatted_price if include_prices else ""
                    }
                    
                    if include_prices:
                        item_data["price"] = price
                    
                    grouped_items.setdefault(group_name, []).append(item_data)
        
        return grouped_items
    
    def scan_all_groups(self, callback_func: Optional[callable] = None) -> List[str]:
        """Scan all menu groups and optionally call a function for each."""
        groups = self.get_all_menu_groups()
        
        logger.info(f"🔍 Found {len(groups)} menu groups")
        
        for group in groups:
            logger.info(f"Processing group: '{group}'")
            if callback_func:
                callback_func(group)
        
        return groups
    
    def get_parsed_menus(self, force_refresh: bool = False) -> List[Menu]:
        """Get parsed menu objects."""
        data = self.get_menu_data(force_refresh)
        
        menus = []
        for menu_data in data.get("menus", []):
            menu = Menu.from_api_data(menu_data)
            menus.append(menu)
        
        return menus
    
    def get_menu_by_name(self, name: str, force_refresh: bool = False) -> Optional[Menu]:
        """Get a specific menu by name."""
        menus = self.get_parsed_menus(force_refresh)
        
        for menu in menus:
            if menu.name.lower() == name.lower():
                return menu
        
        return None

