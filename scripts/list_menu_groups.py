# scripts/list_menu_groups.py
"""List all available menu groups."""
from toast_api.services.menu_service import MenuService
from toast_api.utils.logger import logger

def main():
    """List all menu groups."""
    try:
        menu_service = MenuService()
        groups = menu_service.get_all_menu_groups()
        
        print("\n📚 Available Menu Groups:\n")
        for name in groups:
            print(f"• {name}")
            
    except Exception as e:
        logger.error(f"Error listing menu groups: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
