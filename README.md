# Project Structure
```bash
toast-api/
├── .env                          # Environment variables
├── main.py                       # CLI entry point
├── requirements.txt              # Python dependencies
├── group_order.txt               # Menu group ordering
├── toast_api/                    # Main package
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── client/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── api_client.py
│   │   └── exceptions.py
│   ├── models/
│   │   └── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── menu_service.py
│   └── utils/
│       ├── __init__.py
│       ├── cache.py
│       └── logger.py
└── scripts/
    ├── __init__.py
    ├── list_menu_groups.py
    ├── scan_all_groups.py
    ├── generate_menu.py
    └── menu_group_items.py      # Your existing script
```
# Requirements File (requirements.txt)
```
requests>=2.28.0
python-dotenv>=1.0.0
reportlab>=3.6.0
```
# Setup Requirements
## Contents of .env
```bash
# Toast Tab API Configuration
TOAST_HOSTNAME=https://ws-api.toasttab.com
TOAST_CLIENT_ID=your-client-id
TOAST_CLIENT_SECRET=your-client-secret
TOAST_RESTAURANT_GUID=your-restaurant-guid

# Optional Configuration
TOKEN_CACHE_FILE=token_cache.json
MENU_CACHE_FILE=menu_v2_out.json
API_TIMEOUT=30

# Restaurant Information (for menu generation)
RESTAURANT_NAME=Your Restaurant Name
RESTAURANT_ADDRESS=Address
RESTAURANT_PHONE=999-999-9999
RESTAURANT_WEBSITE=www.myrestaurant.com
```
## Logo file for PDF menu generation
The script uses a file called restaurant_logo.jpeg. This is used to put your logo if one is available in the pdf file generated.

# Installation and Setup
**Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
### Command Line Interface
```bash
# List all menu groups
python main.py list-groups

# Scan all groups (calls your existing processing script)
python main.py scan-groups

# Generate takeout menu with prices
python main.py generate-menu --with-price

# Generate 3rd party delivery menu
python main.py generate-menu --filter-3pd

# Clear all cached data
python main.py clear-cache

# Enable debug logging
python main.py --log-level DEBUG list-groups
```

