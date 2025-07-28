"""
Validation utilities for Toast API client.
"""
import re
from typing import Any, Dict, List, Optional
from datetime import datetime


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove common separators
    cleaned = re.sub(r'[-()\s]', '', phone)
    
    # Check if it's a valid US phone number (10 digits)
    return re.match(r'^\+?1?[0-9]{10}$', cleaned) is not None


def validate_guid(guid: str) -> bool:
    """Validate GUID format."""
    if not guid or not isinstance(guid, str):
        return False
    
    pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    return re.match(pattern, guid) is not None


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Validate that required fields are present and not empty."""
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing_fields.append(field)
    
    return missing_fields


def validate_price(price: Any) -> bool:
    """Validate price value."""
    if price is None:
        return False
    
    try:
        price_float = float(price)
        return price_float >= 0
    except (ValueError, TypeError):
        return False


def validate_date_string(date_string: str, format_string: str = '%Y-%m-%d') -> bool:
    """Validate date string format."""
    if not date_string or not isinstance(date_string, str):
        return False
    
    try:
        datetime.strptime(date_string, format_string)
        return True
    except ValueError:
        return False


def validate_restaurant_guid(restaurant_guid: str) -> bool:
    """Validate restaurant GUID format specifically."""
    return validate_guid(restaurant_guid)


def validate_menu_item_data(item_data: Dict[str, Any]) -> List[str]:
    """Validate menu item data structure."""
    required_fields = ['name', 'price']
    errors = []
    
    # Check required fields
    missing = validate_required_fields(item_data, required_fields)
    errors.extend([f"Missing required field: {field}" for field in missing])
    
    # Validate price if present
    if 'price' in item_data and not validate_price(item_data['price']):
        errors.append("Invalid price value")
    
    return errors


def validate_customer_data(customer_data: Dict[str, Any]) -> List[str]:
    """Validate customer data structure."""
    errors = []
    
    # Validate email if present
    if 'email' in customer_data and customer_data['email']:
        if not validate_email(customer_data['email']):
            errors.append("Invalid email format")
    
    # Validate phone if present
    if 'phone' in customer_data and customer_data['phone']:
        if not validate_phone(customer_data['phone']):
            errors.append("Invalid phone number format")
    
    return errors


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize string input."""
    if not isinstance(value, str):
        return str(value) if value is not None else ''
    
    # Basic sanitization
    sanitized = value.strip()
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_pagination_params(page: int, limit: int, max_limit: int = 100) -> List[str]:
    """Validate pagination parameters."""
    errors = []
    
    if page < 1:
        errors.append("Page must be greater than 0")
    
    if limit < 1:
        errors.append("Limit must be greater than 0")
    
    if limit > max_limit:
        errors.append(f"Limit cannot exceed {max_limit}")
    
    return errors

def validate_url(url: str) -> bool:
    """Validate URL format."""
    if not url or not isinstance(url, str):
        return False

    # Basic URL pattern validation
    pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    return re.match(pattern, url) is not None
