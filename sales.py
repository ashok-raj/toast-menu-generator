#!/usr/bin/env python3
"""
Toast Sales Summary Script
Version: 2.7.0

Features:
- Interactive Toast API sales data retrieval using Toast business dates
- Offline analysis from saved JSON files
- Business date handling for both single dates and date ranges
- Restaurant-standard week reporting (Sunday-Saturday)
- Optional debug mode (-d flag) for raw API data logging
- Comprehensive sales reporting with tips and payment breakdowns
- Proper handling of payment status and void conditions

Author: Assistant
Last Updated: 2025-08-04
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import os
import argparse
from dotenv import load_dotenv
from decimal import Decimal, ROUND_HALF_UP


class ToastSalesAPIClient:
    def __init__(self, hostname: str, client_id: str, client_secret: str, restaurant_guid: str, debug_mode: bool = False):
        """Initialize Toast API client for sales data"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.restaurant_guid = restaurant_guid
        self.debug_mode = debug_mode
        
        # Clean hostname (remove protocol if present)
        if hostname.startswith('https://'):
            self.hostname = hostname.replace('https://', '')
        elif hostname.startswith('http://'):
            self.hostname = hostname.replace('http://', '')
        else:
            self.hostname = hostname
        
        # Set base URLs
        self.auth_base_url = f"https://{self.hostname}"
        self.api_base_url = f"https://{self.hostname}"
        
        self.access_token = None
        self.token_expires_at = None
    
    def authenticate(self) -> bool:
        """Authenticate with Toast API and get access token"""
        auth_url = f"{self.auth_base_url}/authentication/v1/authentication/login"
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "clientId": self.client_id,
            "clientSecret": self.client_secret,
            "userAccessType": "TOAST_MACHINE_CLIENT"
        }
        
        try:
            print(f"Authenticating with: {auth_url}")
            response = requests.post(auth_url, headers=headers, json=payload)
            
            print(f"Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Response content: {response.text}")
            
            response.raise_for_status()
            
            auth_data = response.json()
            self.access_token = auth_data.get("token", {}).get("accessToken")
            
            if self.access_token:
                self.token_expires_at = datetime.now() + timedelta(minutes=55)
                print("Authentication successful")
                return True
            else:
                print("Authentication failed: No access token received")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Authentication error: {e}")
            return False
    
    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid access token"""
        if not self.access_token or (self.token_expires_at and datetime.now() >= self.token_expires_at):
            return self.authenticate()
        return True
    
    def _format_business_date(self, date_str: str) -> str:
        """Format date string for Toast API business date parameter"""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%Y%m%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Please use YYYY-MM-DD format.")
    
    def get_orders_by_business_date(self, business_date: str) -> Optional[List[Dict]]:
        """Retrieve orders for a specific business date"""
        if not self._ensure_authenticated():
            print("Failed to authenticate")
            return None
        
        try:
            formatted_business_date = self._format_business_date(business_date)
        except ValueError as e:
            print(f"Date formatting error: {e}")
            return None
        
        print(f"Using business date: {formatted_business_date} (from {business_date})")
        
        url = f"{self.api_base_url}/orders/v2/ordersBulk"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Toast-Restaurant-External-ID": self.restaurant_guid,
            "Content-Type": "application/json"
        }
        params = {
            "businessDate": formatted_business_date,
            "pageSize": 100
        }
        
        all_orders = []
        page = 1
        
        while True:
            if page > 1:
                params["page"] = page
            
            try:
                print(f"Fetching orders page {page} (current total: {len(all_orders)})...")
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code != 200:
                    print(f"API Error - Status: {response.status_code}")
                    print(f"Response content: {response.text}")
                
                response.raise_for_status()
                
                data = response.json()
                orders = data if isinstance(data, list) else []
                all_orders.extend(orders)
                
                # Save debug file only if debug mode is enabled
                if self.debug_mode:
                    debug_filename = f"debug_orders_business_date_{formatted_business_date}_page_{page}.json"
                    try:
                        with open(debug_filename, 'w') as f:
                            json.dump({
                                'page': page,
                                'business_date': {
                                    'input_date': business_date,
                                    'formatted_business_date': formatted_business_date
                                },
                                'request_params': params,
                                'orders_count': len(orders),
                                'orders': data
                            }, f, indent=2)
                        print(f"DEBUG: Saved page {page} raw data to {debug_filename}")
                    except Exception as e:
                        print(f"Warning: Could not save debug file: {e}")
                
                if len(orders) < params["pageSize"]:
                    break
                
                page += 1
                
            except requests.exceptions.RequestException as e:
                print(f"Error retrieving orders: {e}")
                return None
        
        print(f"Retrieved {len(all_orders)} total orders for business date {formatted_business_date}")
        return all_orders

    def get_orders_by_date_range(self, start_date: str, end_date: str) -> Optional[List[Dict]]:
        """Retrieve orders for a date range using business dates"""
        print(f"Using business date range method: {start_date} to {end_date}")
        
        all_orders = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        while current_date <= end_dt:
            date_str = current_date.strftime("%Y-%m-%d")
            print(f"Fetching business date: {date_str}")
            
            orders = self.get_orders_by_business_date(date_str)
            if orders:
                all_orders.extend(orders)
            
            current_date += timedelta(days=1)
        
        print(f"Retrieved {len(all_orders)} total orders across business date range")
        return all_orders


class SalesSummaryAnalyzer:
    def __init__(self):
        self.orders = []
    
    def analyze_sales_summary(self, orders: List[Dict]) -> Dict:
        """Analyze orders to create sales summary"""
        self.orders = orders
        
        summary = {
            'total_orders': len(orders),
            'total_payments': 0,
            'gross_sales': Decimal('0.00'),
            'net_sales': Decimal('0.00'),
            'total_tips': Decimal('0.00'),
            'total_tax': Decimal('0.00'),
            'total_discounts': Decimal('0.00'),
            'payment_breakdown': {},
            'daily_breakdown': {},
            'order_types': {},
            'voided_orders': 0,
            'refunded_amount': Decimal('0.00')
        }
        
        # Analyze orders
        for order in orders:
            order_date = self._extract_date_from_order(order)
            order_type = order.get('source', 'Unknown')
            
            # Initialize daily breakdown
            if order_date not in summary['daily_breakdown']:
                summary['daily_breakdown'][order_date] = {
                    'orders': 0,
                    'gross_sales': Decimal('0.00'),
                    'tips': Decimal('0.00'),
                    'tax': Decimal('0.00')
                }
            
            # Count order types
            summary['order_types'][order_type] = summary['order_types'].get(order_type, 0) + 1
            
            # Check if order is voided
            if order.get('voided', False):
                summary['voided_orders'] += 1
                continue
            
            # Process each check in the order
            checks = order.get('checks', [])
            for check in checks:
                if check.get('voided', False):
                    continue
                
                # Get tax amount from check
                tax_amount = Decimal(str(check.get('taxAmount', 0)))
                summary['total_tax'] += tax_amount
                
                # Initialize check totals
                check_gross_sales = Decimal('0.00')
                check_tips = Decimal('0.00')
                
                # Process payments for this check
                payments = check.get('payments', [])
                for payment in payments:
                    # Check payment status and void conditions
                    payment_status = payment.get('paymentStatus', 'UNKNOWN')
                    is_voided = payment.get('voided', False)
                    
                    # Skip payments that are truly voided
                    # If payment status is OPEN and voided is True, don't treat as voided
                    if is_voided and payment_status != 'OPEN':
                        continue
                    
                    payment_type = payment.get('type', 'Unknown')
                    
                    # Toast API returns amounts in dollars (not cents)
                    payment_amount = Decimal(str(payment.get('amount', 0)))
                    tip_amount = Decimal(str(payment.get('tipAmount', 0)))
                    
                    # Debug output for first few payments
                    if summary['total_payments'] < 3:
                        print(f"DEBUG - Payment {summary['total_payments'] + 1}:")
                        print(f"  Payment amount: ${payment_amount}")
                        print(f"  Tip amount: ${tip_amount}")
                        print(f"  Payment type: {payment_type}")
                        print(f"  Payment status: {payment_status}")
                        print(f"  Voided flag: {is_voided}")
                        print(f"  Including in summary: {not (is_voided and payment_status != 'OPEN')}")
                    
                    summary['total_payments'] += 1
                    
                    # Gross sales = payment amount + tip amount
                    check_gross_sales += payment_amount + tip_amount
                    check_tips += tip_amount
                    
                    # Payment method breakdown
                    if payment_type not in summary['payment_breakdown']:
                        summary['payment_breakdown'][payment_type] = {
                            'count': 0,
                            'amount': Decimal('0.00'),
                            'tips': Decimal('0.00')
                        }
                    
                    summary['payment_breakdown'][payment_type]['count'] += 1
                    summary['payment_breakdown'][payment_type]['amount'] += payment_amount
                    summary['payment_breakdown'][payment_type]['tips'] += tip_amount
                
                # Add to totals
                summary['gross_sales'] += check_gross_sales
                summary['total_tips'] += check_tips
                
                # Daily breakdown (only count if there were payments)
                if check_gross_sales > 0:
                    summary['daily_breakdown'][order_date]['orders'] += 1
                    summary['daily_breakdown'][order_date]['gross_sales'] += check_gross_sales
                    summary['daily_breakdown'][order_date]['tips'] += check_tips
                    summary['daily_breakdown'][order_date]['tax'] += tax_amount
        
        # Calculate net sales
        summary['net_sales'] = summary['gross_sales'] - summary['total_tax'] - summary['total_discounts']
        
        return summary
    
    def _extract_date_from_order(self, order: Dict) -> str:
        """Extract date from order timestamp"""
        try:
            timestamp = order.get('openedDate') or order.get('closedDate') or order.get('createdDate')
            if timestamp:
                if 'T' in timestamp:
                    return timestamp.split('T')[0]
                return timestamp[:10]
            return 'Unknown'
        except:
            return 'Unknown'


def load_orders_from_json(filename: str) -> Optional[List[Dict]]:
    """Load orders from a saved JSON file"""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            orders = data
        elif isinstance(data, dict):
            if 'orders' in data:
                orders = data['orders']
            elif 'data' in data:
                orders = data['data']
            else:
                orders = [data]
        else:
            print(f"Unexpected JSON format in {filename}")
            return None
        
        print(f"Loaded {len(orders)} orders from {filename}")
        return orders
        
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return None
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {filename}: {e}")
        return None
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None


def get_data_source_choice() -> str:
    """Ask user whether to use Toast API or load from JSON file"""
    print("\n" + "="*50)
    print("DATA SOURCE SELECTION")
    print("="*50)
    print("1. Fetch data from Toast API (live)")
    print("2. Load data from saved JSON file (offline)")
    print("-" * 50)
    
    while True:
        choice = input("Enter your choice (1-2): ").strip()
        if choice == '1':
            return 'api'
        elif choice == '2':
            return 'json'
        else:
            print("Invalid choice. Please enter 1 or 2.")


def get_date_input_method() -> str:
    """Ask user whether to use single business date or business date range"""
    print("\n" + "="*50)
    print("DATE SELECTION METHOD")
    print("="*50)
    print("1. Single business date")
    print("   - Analyze one complete business day")
    print("   - Perfect for daily reporting")
    print()
    print("2. Business date range")
    print("   - Analyze multiple business days")
    print("   - Great for weekly/monthly reporting")
    print("   - Uses business dates for each day")
    print("-" * 50)
    
    while True:
        choice = input("Enter your choice (1-2): ").strip()
        if choice == '1':
            return 'business'
        elif choice == '2':
            return 'range'
        else:
            print("Invalid choice. Please enter 1 or 2.")


def get_business_date_input() -> str:
    """Get single business date from user"""
    print("\n" + "="*50)
    print("BUSINESS DATE SELECTION")
    print("="*50)
    print("Enter the business date you want to analyze.")
    print("Note: This represents one complete business day cycle")
    print("(e.g., from opening to closing, even if it spans midnight)")
    print()
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    print("Quick options:")
    print(f"1. Today ({today})")
    print(f"2. Yesterday ({yesterday})")
    print("3. Enter custom date")
    print("-" * 50)
    
    while True:
        choice = input("Enter your choice (1-3): ").strip()
        if choice == '1':
            return str(today)
        elif choice == '2':
            return str(yesterday)
        elif choice == '3':
            while True:
                date_str = input("Enter business date (YYYY-MM-DD): ").strip()
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                    return date_str
                except ValueError:
                    print("Invalid date format. Please use YYYY-MM-DD format.")
        else:
            print("Invalid choice. Please enter 1-3.")


def get_json_file_input() -> str:
    """Get JSON filename from user"""
    print("\nAvailable JSON files in current directory:")
    
    json_files = [f for f in os.listdir('.') if f.endswith('.json')]
    if json_files:
        for i, filename in enumerate(json_files, 1):
            print(f"  {i}. {filename}")
        print()
    else:
        print("  No JSON files found in current directory")
        print()
    
    while True:
        filename = input("Enter JSON filename (or full path): ").strip()
        filename = filename.strip('"\'')
        
        if os.path.exists(filename):
            return filename
        else:
            print(f"File not found: {filename}")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != 'y':
                return ""


def get_date_range_input() -> Tuple[str, str]:
    """Get business date range input from user"""
    print("\n" + "="*50)
    print("BUSINESS DATE RANGE SELECTION")
    print("="*50)
    print("Select the range of business dates to analyze.")
    print("Each date represents a complete business day cycle.")
    print()
    
    print("Choose an option:")
    print("1. Custom date range")
    print("2. Pre-set sales periods")
    
    while True:
        choice = input("Enter your choice (1-2): ").strip()
        if choice in ['1', '2']:
            break
        print("Invalid choice. Please enter 1 or 2.")
    
    if choice == '1':
        # Custom date range
        print("\nCustom Business Date Range:")
        while True:
            start_date = input("Enter start business date (YYYY-MM-DD): ").strip()
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                break
            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD format.")
        
        while True:
            end_date = input("Enter end business date (YYYY-MM-DD): ").strip()
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                if end_dt < start_dt:
                    print("End date must be after start date.")
                    continue
                return start_date, end_date
            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD format.")
    
    else:
        # Pre-set sales periods
        today = datetime.now().date()
        
        # Calculate Sunday-Saturday weeks
        days_since_sunday = (today.weekday() + 1) % 7  # Monday=0, Sunday=6 -> Sunday=0
        this_week_start = today - timedelta(days=days_since_sunday)  # This Sunday
        this_week_end = today  # Today
        
        # Previous week (Sunday to Saturday)
        prev_week_start = this_week_start - timedelta(days=7)  # Previous Sunday
        prev_week_end = this_week_start - timedelta(days=1)    # Previous Saturday
        
        # Month calculations
        month_start = today.replace(day=1)
        if today.month == 1:
            last_month_start = today.replace(year=today.year-1, month=12, day=1)
            last_month_end = today.replace(day=1) - timedelta(days=1)
        else:
            last_month_start = today.replace(month=today.month-1, day=1)
            # Get last day of previous month
            next_month = today.replace(day=1)
            last_month_end = next_month - timedelta(days=1)
        
        print("\nPre-set Sales Periods:")
        print(f"1. This week - Sunday to today ({this_week_start} to {this_week_end})")
        print(f"2. Previous week - Sunday to Saturday ({prev_week_start} to {prev_week_end})")
        print(f"3. This month - 1st to today ({month_start} to {today})")
        print(f"4. Last month - complete ({last_month_start} to {last_month_end})")
        print(f"5. Last 7 days ({today - timedelta(days=6)} to {today})")
        print(f"6. Last 30 days ({today - timedelta(days=29)} to {today})")
        
        while True:
            quick_choice = input("Enter your choice (1-6): ").strip()
            if quick_choice == '1':
                return str(this_week_start), str(this_week_end)
            elif quick_choice == '2':
                return str(prev_week_start), str(prev_week_end)
            elif quick_choice == '3':
                return str(month_start), str(today)
            elif quick_choice == '4':
                return str(last_month_start), str(last_month_end)
            elif quick_choice == '5':
                return str(today - timedelta(days=6)), str(today)
            elif quick_choice == '6':
                return str(today - timedelta(days=29)), str(today)
            else:
                print("Invalid choice. Please enter 1-6.")


def format_currency(amount: Decimal) -> str:
    """Format decimal amount as currency"""
    return f"${amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"


def display_sales_summary(summary: Dict, start_date: str, end_date: str) -> None:
    """Display formatted sales summary"""
    print(f"\n{'='*80}")
    print(f"SALES SUMMARY: {start_date} to {end_date}")
    print(f"{'='*80}")
    
    # Overall totals
    print(f"\n📊 OVERALL TOTALS:")
    print(f"   Total Orders: {summary['total_orders']:,}")
    print(f"   Voided Orders: {summary['voided_orders']:,}")
    print(f"   Gross Sales: {format_currency(summary['gross_sales'])}")
    print(f"   Total Tax: {format_currency(summary['total_tax'])}")
    print(f"   Total Tips: {format_currency(summary['total_tips'])}")
    print(f"   Net Sales: {format_currency(summary['net_sales'])}")
    
    # Daily breakdown
    if summary['daily_breakdown']:
        print(f"\n📅 DAILY BREAKDOWN:")
        print(f"   {'Date':<12} {'Orders':<8} {'Gross Sales':<15} {'Tips':<12} {'Tax':<12}")
        print(f"   {'-'*60}")
        
        total_daily_orders = 0
        total_daily_sales = Decimal('0.00')
        total_daily_tips = Decimal('0.00')
        total_daily_tax = Decimal('0.00')
        
        for date in sorted(summary['daily_breakdown'].keys()):
            if date != 'Unknown':
                day_data = summary['daily_breakdown'][date]
                orders = day_data['orders']
                sales = day_data['gross_sales']
                tips = day_data['tips']
                tax = day_data['tax']
                
                print(f"   {date:<12} {orders:<8} {format_currency(sales):<15} {format_currency(tips):<12} {format_currency(tax):<12}")
                
                total_daily_orders += orders
                total_daily_sales += sales
                total_daily_tips += tips
                total_daily_tax += tax
        
        print(f"   {'-'*60}")
        print(f"   {'TOTAL':<12} {total_daily_orders:<8} {format_currency(total_daily_sales):<15} {format_currency(total_daily_tips):<12} {format_currency(total_daily_tax):<12}")
    
    # Payment method breakdown
    if summary['payment_breakdown']:
        print(f"\n💳 PAYMENT METHOD BREAKDOWN:")
        print(f"   {'Method':<15} {'Count':<8} {'Amount':<15} {'Tips':<12}")
        print(f"   {'-'*50}")
        
        for method, data in summary['payment_breakdown'].items():
            count = data['count']
            amount = data['amount']
            tips = data['tips']
            print(f"   {method:<15} {count:<8} {format_currency(amount):<15} {format_currency(tips):<12}")
    
    # Order type breakdown
    if summary['order_types']:
        print(f"\n🍽️  ORDER TYPE BREAKDOWN:")
        for order_type, count in summary['order_types'].items():
            percentage = (count / summary['total_orders'] * 100) if summary['total_orders'] > 0 else 0
            print(f"   {order_type}: {count:,} orders ({percentage:.1f}%)")


def load_config() -> Dict[str, str]:
    """Load configuration from .env file"""
    load_dotenv()
    
    config = {
        'hostname': os.getenv('TOAST_HOSTNAME'),
        'client_id': os.getenv('TOAST_CLIENT_ID'),
        'client_secret': os.getenv('TOAST_CLIENT_SECRET'),
        'restaurant_guid': os.getenv('TOAST_RESTAURANT_GUID')
    }
    
    missing_values = [key for key, value in config.items() if not value]
    if missing_values:
        print(f"Error: Missing required environment variables: {', '.join(missing_values)}")
        print("\nPlease create a .env file with the following variables:")
        print("TOAST_HOSTNAME=ws-sandbox-api.toasttab.com")
        print("TOAST_CLIENT_ID=your_client_id")
        print("TOAST_CLIENT_SECRET=your_client_secret")
        print("TOAST_RESTAURANT_GUID=your_restaurant_guid")
        print("\nNote: Hostname should NOT include 'https://' - just the hostname")
        return None
    
    return config


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Toast Sales Summary Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python sales.py                    # Normal mode (no debug files)
  python sales.py -d                 # Debug mode (saves raw API responses)
  python sales.py --debug            # Debug mode (long form)
        '''
    )
    
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Enable debug mode to save raw API responses to JSON files'
    )
    
    return parser.parse_args()


def main():
    """Main function with interactive interface"""
    # Parse command line arguments
    args = parse_arguments()
    
    print("="*60)
    print("TOAST SALES SUMMARY SCRIPT v2.7.0")
    if args.debug:
        print("DEBUG MODE: Raw API responses will be saved to JSON files")
    print("="*60)
    
    # Choose data source
    data_source = get_data_source_choice()
    
    if data_source == 'api':
        # Load configuration
        config = load_config()
        if not config:
            return
        
        # Initialize client
        client = ToastSalesAPIClient(
            hostname=config['hostname'],
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            restaurant_guid=config['restaurant_guid'],
            debug_mode=args.debug
        )
        
        print(f"Connecting to Toast API server: https://{client.hostname}")
        
        # Test authentication
        print("Testing authentication...")
        if not client.authenticate():
            print("Authentication failed. Please check your credentials and hostname.")
            return
    
    analyzer = SalesSummaryAnalyzer()
    
    while True:
        try:
            if data_source == 'api':
                # Choose date method
                date_method = get_date_input_method()
                
                if date_method == 'business':
                    # Get single business date
                    business_date = get_business_date_input()
                    
                    print(f"\nFetching sales data for business date: {business_date}")
                    
                    # Fetch orders for business date
                    orders = client.get_orders_by_business_date(business_date)
                    
                    start_date = business_date
                    end_date = business_date
                    date_range_str = f"business_date_{business_date}"
                    
                else:  # date_method == 'range'
                    # Get date range
                    start_date, end_date = get_date_range_input()
                    
                    print(f"\nFetching sales data from {start_date} to {end_date}...")
                    
                    # Fetch orders for date range
                    orders = client.get_orders_by_date_range(start_date, end_date)
                    
                    date_range_str = f"{start_date}_to_{end_date}"
                
                if orders is None:
                    print("Failed to retrieve sales data.")
                    continue
                    
            else:  # data_source == 'json'
                # Get JSON file from user
                json_filename = get_json_file_input()
                if not json_filename:
                    print("No file selected. Exiting.")
                    return
                
                print(f"\nLoading sales data from {json_filename}...")
                orders = load_orders_from_json(json_filename)
                
                if orders is None:
                    print("Failed to load sales data from file.")
                    continue
                
                # Extract date range from filename
                base_filename = os.path.basename(json_filename).replace('.json', '')
                date_range_str = base_filename
                start_date = "unknown"
                end_date = "unknown"
            
            # Generate summary
            print("Analyzing sales data...")
            summary = analyzer.analyze_sales_summary(orders)
            
            # Display results
            display_sales_summary(summary, start_date, end_date)
            
            # Ask if user wants to save results
            save_choice = input("\nWould you like to save this summary to a file? (y/n): ").strip().lower()
            if save_choice == 'y':
                if data_source == 'api':
                    filename = f"sales_summary_{date_range_str}.json"
                    summary_data = {
                        'date_range': {'start': start_date, 'end': end_date},
                        'summary': json.loads(json.dumps(summary, default=lambda x: float(x) if isinstance(x, Decimal) else str(x))),
                        'raw_orders_count': len(orders),
                        'data_source': 'toast_api'
                    }
                else:
                    filename = f"sales_summary_{date_range_str}_from_json.json"
                    summary_data = {
                        'source_file': json_filename,
                        'summary': json.loads(json.dumps(summary, default=lambda x: float(x) if isinstance(x, Decimal) else str(x))),
                        'raw_orders_count': len(orders),
                        'data_source': 'json_file'
                    }
                
                try:
                    with open(filename, 'w') as f:
                        json.dump(summary_data, f, indent=2)
                    print(f"Sales summary saved to {filename}")
                except Exception as e:
                    print(f"Error saving file: {e}")
            
            # Ask if user wants to continue
            if data_source == 'api':
                continue_choice = input("\nWould you like to generate another summary? (y/n): ").strip().lower()
            else:
                continue_choice = input("\nWould you like to analyze another file? (y/n): ").strip().lower()
                
            if continue_choice != 'y':
                print("Goodbye!")
                break
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            continue


if __name__ == "__main__":
    main()
