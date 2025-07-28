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
