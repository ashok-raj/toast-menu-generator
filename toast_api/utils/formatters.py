# toast_api/utils/formatters.py
"""Data formatting utilities."""
from typing import Any, Dict, List
from datetime import datetime

def format_currency(amount: float, currency_symbol: str = "$") -> str:
    """Format a number as currency."""
    if amount is None:
        return ""
    return f"{currency_symbol}{amount:.2f}"

def format_percentage(value: float, decimal_places: int = 1) -> str:
    """Format a decimal as percentage."""
    if value is None:
        return ""
    return f"{value * 100:.{decimal_places}f}%"

def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a datetime object."""
    if dt is None:
        return ""
    return dt.strftime(format_str)

def format_phone_number(phone: str) -> str:
    """Format a phone number for display."""
    if not phone:
        return ""
    
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    # Format as (XXX) XXX-XXXX if 10 digits
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    
    # Return as-is if not 10 digits
    return phone

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to a maximum length."""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def format_list_display(items: List[str], max_items: int = 5, separator: str = ", ") -> str:
    """Format a list for display, truncating if too long."""
    if not items:
        return ""
    
    if len(items) <= max_items:
        return separator.join(items)
    
    displayed = items[:max_items]
    remaining = len(items) - max_items
    return separator.join(displayed) + f" and {remaining} more"

def format_menu_item_display(name: str, price: float = None, max_name_length: int = 40) -> str:
    """Format a menu item for display."""
    truncated_name = truncate_text(name, max_name_length)
    
    if price is not None:
        price_str = format_currency(price)
        return f"{truncated_name:<{max_name_length}} {price_str:>8}"
    
    return truncated_name

def sanitize_filename(filename: str) -> str:
    """Sanitize a string to be safe for use as a filename."""
    import re
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')
    return sanitized
