# Directory Structure
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
# Contents of .env
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
RESTAURANT_NAME=ChennaiMasala
RESTAURANT_ADDRESS=2088 NE Stucki Ave, Hillsboro, OR 97124
RESTAURANT_PHONE=503-531-9500
RESTAURANT_WEBSITE=www.chennaimasala.net
```
