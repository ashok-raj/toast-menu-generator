# scripts/scan_all_groups.py  
"""Scan all menu groups and process them."""
import subprocess
from toast_api.services.menu_service import MenuService
from toast_api.utils.logger import logger

def process_group(group_name: str) -> None:
    """Process a single menu group."""
    logger.info(f"🔍 Scanning group: '{group_name}'")
    # Call your existing menu_group_items.py script
    subprocess.run(["python", "menu_group_items.py", group_name, ""])

def main():
    """Scan all menu groups."""
    try:
        menu_service = MenuService()
        groups = menu_service.scan_all_groups(callback_func=process_group)
        
        logger.info(f"✅ Processed {len(groups)} menu groups")
        
    except Exception as e:
        logger.error(f"Error scanning groups: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())


