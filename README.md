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
requests==2.32.5
python-dotenv==1.1.1
reportlab>=3.6.0
```
This has been only tested on Ubuntu. I was also able to get it to work in MacOS using brew and pip to install the required extensions.
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

## Sales Analysis Script

### sales.py
A comprehensive Toast sales analysis script that provides detailed sales summaries and reporting.

**Features:**
- Interactive Toast API sales data retrieval using Toast business dates
- Offline analysis from saved JSON files
- Business date handling for both single dates and date ranges
- Restaurant-standard week reporting (Sunday-Saturday)
- Optional debug mode (-d flag) for raw API data logging
- Comprehensive sales reporting with tips and payment breakdowns
- Proper handling of payment status and void conditions

**Usage Examples:**
```bash
# Today's sales (display only)
python sales.py --today

# Yesterday's complete report
python sales.py --yesterday --all

# Current week (Sunday to today)
python sales.py --this-week

# Complete previous week (Sun-Sat)
python sales.py --last-week

# Current month (1st to today)
python sales.py --this-month

# Complete previous month
python sales.py --last-month

# Current year (Jan 1st to today)
python sales.py --this-year

# Complete previous year
python sales.py --last-year

# Custom date range
python sales.py --range 2025-08-01 2025-08-15

# Save to JSON file
python sales.py --today --file my_report.json

# Debug mode (saves raw API responses)
python sales.py --today --debug
```

**Installation:**
Use the same virtual environment setup as the main project:
```bash
source ~/.python/araj-venv/bin/activate
pip install -r requirements.txt
python sales.py --today
```

