# toast_api/models/menu.py
"""Menu data models."""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class MenuItem:
    """Represents a menu item."""
    guid: str
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    calories: Optional[int] = None
    is_available: bool = True
    images: List[str] = None
    modifiers: List[str] = None
    tags: List[str] = None
    raw_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.images is None:
            self.images = []
        if self.modifiers is None:
            self.modifiers = []
        if self.tags is None:
            self.tags = []
        if self.raw_data is None:
            self.raw_data = {}
    
    @property
    def formatted_price(self) -> str:
        """Get formatted price string."""
        if self.price is not None:
            return f"${self.price:.2f}"
        return ""
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'MenuItem':
        """Create MenuItem from Toast API data."""
        return cls(
            guid=data.get("guid", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            price=data.get("price"),
            calories=data.get("calories"),
            is_available=data.get("isAvailable", True),
            images=data.get("images", []),
            modifiers=data.get("modifiers", []),
            tags=data.get("tags", []),
            raw_data=data
        )

@dataclass
class MenuGroup:
    """Represents a menu group (category)."""
    guid: str
    name: str
    description: Optional[str] = None
    display_order: int = 0
    visibility: List[str] = None
    items: List[MenuItem] = None
    raw_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.visibility is None:
            self.visibility = []
        if self.items is None:
            self.items = []
        if self.raw_data is None:
            self.raw_data = {}
    
    @property
    def is_visible_to_partners(self) -> bool:
        """Check if group is visible to ordering partners (3rd party)."""
        return "ORDERING_PARTNERS" in self.visibility
    
    def add_item(self, item: MenuItem) -> None:
        """Add a menu item to this group."""
        self.items.append(item)
    
    def get_available_items(self) -> List[MenuItem]:
        """Get only available items."""
        return [item for item in self.items if item.is_available]
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'MenuGroup':
        """Create MenuGroup from Toast API data."""
        group = cls(
            guid=data.get("guid", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            display_order=data.get("displayOrder", 0),
            visibility=data.get("visibility", []),
            raw_data=data
        )
        
        # Add menu items
        for item_data in data.get("menuItems", []):
            item = MenuItem.from_api_data(item_data)
            group.add_item(item)
        
        return group

@dataclass
class Menu:
    """Represents a complete menu."""
    guid: str
    name: str
    description: Optional[str] = None
    is_master_menu: bool = False
    groups: List[MenuGroup] = None
    raw_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.groups is None:
            self.groups = []
        if self.raw_data is None:
            self.raw_data = {}
    
    @property
    def is_third_party_menu(self) -> bool:
        """Check if this is a 3rd party delivery menu."""
        return "3pd" in self.name.lower()
    
    @property
    def should_skip_menu(self) -> bool:
        """Check if this menu should be skipped based on name."""
        skip_terms = ["owner", "otter", "happy", "beer", "catering", "weekend"]
        return any(term in self.name.lower() for term in skip_terms)
    
    def add_group(self, group: MenuGroup) -> None:
        """Add a menu group to this menu."""
        self.groups.append(group)
    
    def get_group_by_name(self, name: str) -> Optional[MenuGroup]:
        """Get a menu group by name."""
        for group in self.groups:
            if group.name == name:
                return group
        return None
    
    def get_all_group_names(self) -> List[str]:
        """Get all group names in this menu."""
        return [group.name for group in self.groups]
    
    def get_items_by_group(self, group_name: str) -> List[MenuItem]:
        """Get all items in a specific group."""
        group = self.get_group_by_name(group_name)
        return group.items if group else []
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> 'Menu':
        """Create Menu from Toast API data."""
        menu = cls(
            guid=data.get("guid", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            is_master_menu=data.get("masterMenu", False),
            raw_data=data
        )
        
        # Add menu groups
        for group_data in data.get("menuGroups", []):
            group = MenuGroup.from_api_data(group_data)
            menu.add_group(group)
        
        return menu
