# toast_api/models/restaurant.py
"""Restaurant data models."""
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Restaurant:
    """Represents restaurant information."""
    guid: str
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[str] = None
    timezone: Optional[str] = None
    raw_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.raw_data is None:
            self.raw_data = {}
    
    @property
    def formatted_contact(self) -> str:
        """Get formatted contact information."""
        parts = []
        if self.phone:
            parts.append(self.phone)
        if self.website:
            parts.append(self.website)
        return " • ".join(parts)
    
    @classmethod
    def from_config(cls, config) -> 'Restaurant':
        """Create Restaurant from configuration."""
        return cls(
            guid=config.restaurant_guid,
            name=config.restaurant_name,
            address=config.restaurant_address,
            phone=config.restaurant_phone,
            website=config.restaurant_website
        )


