"""Menu-related business logic and operations."""
from typing import Dict, List, Any, Optional
from ..client.api_client import ToastAPIClient
from ..utils.cache import DataCache
from ..config.settings import config
from ..utils.logger import logger
from ..models.menu import Menu, MenuGroup, MenuItem
import os
import json

class MenuService:
    """Service for menu operations."""
    
    def __init__(self, use_cache: bool = True):
        self.api_client = ToastAPIClient()
        self.use_cache = use_cache
        self.data_cache = DataCache(config.menu_cache_file) if use_cache else None
        self.load_menu_data()

    def load_menu_data(self):
        """Load menu data from JSON file"""
        menu_file = "menu_v2_out.json"
        
        if os.path.exists(menu_file):
            try:
                with open(menu_file, 'r') as f:
                    self.menu_data = json.load(f)
                print(f"✓ Loaded menu data from {menu_file}")
            except Exception as e:
                print(f"❌ Error loading menu data: {e}")
                self.menu_data = None
        else:
            print(f"❌ Menu file {menu_file} not found")
            self.menu_data = None
    
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
    
    def clear_cache(self):
        """ Clear any cached data """
        #Add cache clear logic here
        cache_files = ['menu_v2_out.json', 'token_cache.json']
        for cache_file in cache_files:
            if os.path.exists(cache_file):
                os.remove(cache_file)
                logger.info(f"Removed cache file: {cache_file}") 

        logger.info("Cache cleared successfully")

    def search_items_by_name(self, search_term):
        """Search for menu items by name"""
        if not hasattr(self, 'menu_data') or not self.menu_data:
            print("❌ No menu data available. Load menu data first.")
            return []

        found_items = []
        search_term_lower = search_term.lower()

        # Search through all menus
        for menu in self.menu_data.get("menus", []):
            menu_name = menu.get("name", "")

            # Skip 3pd, owner, otter menus (unless you want to include them)
            if any(term in menu_name.lower() for term in ["3pd", "owner", "otter"]):
                continue

            for group in menu.get("menuGroups", []):
                group_name = group.get("name", "")

                for item in group.get("menuItems", []):
                    item_name = item.get("name", "")

                    # Check if search term is in item name (case insensitive)
                    if search_term_lower in item_name.lower():
                        price = item.get("price")
                        price_str = f"${price:.2f}" if price is not None else "N/A"

                        found_items.append({
                            'name': item_name,
                            'price': price_str,
                            'group': group_name,
                            'menu': menu_name
                        })

            # Display results
            if found_items:
                print(f"✅ Found {len(found_items)} item(s) matching '{search_term}':")
                print("-" * 60)

                for item in found_items:
                    print(f"✓ {item['name']}")
                    print(f"  Price: {item['price']}")
                    print(f"  Category: {item['group']}")
                    print(f"  Menu: {item['menu']}")
                    print()
            else:
                print(f"❌ No items found matching '{search_term}'")

        return found_items

    def get_items_with_images(self, include_3pd: bool = False, format: str = 'text') -> List[Dict[str, Any]]:
        """Get all menu items with their images from Toast Config API."""
        try:
            # Fetch menu items with images from Config API
            config_data = self.api_client.get_menu_items_with_images()

            # Also get regular menu data to match groups
            menu_data = self.get_menu_data()

            # Build group mapping from regular menu data
            group_mapping = {}
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
                    group_name = group.get("name", "")
                    visibility = group.get("visibility", [])

                    # Check visibility for 3pd
                    if include_3pd and "ORDERING_PARTNERS" not in visibility:
                        continue

                    for item in group.get("menuItems", []):
                        item_guid = item.get("guid", "")
                        if item_guid:
                            group_mapping[item_guid] = {
                                'group': group_name,
                                'menu': menu.get("name", "")
                            }

            # Process config API results
            items_with_images = []

            for item in config_data:
                item_guid = item.get("guid", "")
                item_name = item.get("name", "")
                raw_images = item.get("images", [])
                price = item.get("price")
                formatted_price = f"${price:.2f}" if price is not None else ""

                # Extract URLs from image objects
                images = []
                for img in raw_images:
                    if isinstance(img, dict) and 'url' in img:
                        images.append(img['url'])
                    elif isinstance(img, str):
                        images.append(img)

                # Get group info from mapping
                group_info = group_mapping.get(item_guid, {})

                # Only include items that are in our filtered menus
                if group_info or not group_mapping:  # Include all if no filtering
                    item_data = {
                        'guid': item_guid,
                        'name': item_name,
                        'images': images,
                        'price': price,
                        'formatted_price': formatted_price,
                        'group': group_info.get('group', ''),
                        'menu': group_info.get('menu', '')
                    }
                    items_with_images.append(item_data)

            logger.info(f"✅ Found {len(items_with_images)} menu items with image data")
            return items_with_images

        except Exception as e:
            logger.error(f"Error fetching items with images: {e}")
            return []
