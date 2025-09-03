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
            if self.debug_mode:
                print(f"Authenticating with: {auth_url}")
            response = requests.post(auth_url, headers=headers, json=payload)
            
            if self.debug_mode:
                print(f"Response status: {response.status_code}")
                if response.status_code != 200:
                    print(f"Response content: {response.text}")
            
            response.raise_for_status()
            
            auth_data = response.json()
            self.access_token = auth_data.get("token", {}).get("accessToken")
            
            if self.access_token:
                self.token_expires_at = datetime.now() + timedelta(minutes=55)
                if self.debug_mode:
                    print("Authentication successful")
                return True
            else:
                if self.debug_mode:
                    print("Authentication failed: No access token received")
                return False
                
        except requests.exceptions.RequestException as e:
            if self.debug_mode:
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
            if self.debug_mode:
                print(f"Date formatting error: {e}")
            return None
        
        if self.debug_mode:
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
                if self.debug_mode:
                    print(f"Fetching orders page {page} (current total: {len(all_orders)})...")
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code != 200:
                    if self.debug_mode:
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
                        print(f"Debug: Saved page {page} raw data to {debug_filename}")
                    except Exception as e:
                        print(f"Warning: Could not save debug file: {e}")
                
                if len(orders) < params["pageSize"]:
                    break
                
                page += 1
                
            except requests.exceptions.RequestException as e:
                if self.debug_mode:
                    print(f"Error retrieving orders: {e}")
                return None
        
        if self.debug_mode:
            print(f"Retrieved {len(all_orders)} total orders for business date {formatted_business_date}")
        return all_orders

    def get_orders_by_date_range(self, start_date: str, end_date: str) -> Optional[List[Dict]]:
        """Retrieve orders for a date range using business dates"""
        if self.debug_mode:
            print(f"Using business date range method: {start_date} to {end_date}")
        
        all_orders = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        while current_date <= end_dt:
            date_str = current_date.strftime("%Y-%m-%d")
            if self.debug_mode:
                print(f"Fetching business date: {date_str}")
            
            orders = self.get_orders_by_business_date(date_str)
            if orders:
                all_orders.extend(orders)
            
            current_date += timedelta(days=1)
        
        if self.debug_mode:
            print(f"Retrieved {len(all_orders)} total orders across business date range")
        return all_orders
    
    def get_analytics_data(self, business_date: str) -> Optional[Dict]:
        """Retrieve analytics data for a specific business date using the analytics endpoint"""
        if not self._ensure_authenticated():
            print("Failed to authenticate")
            return None
        
        try:
            formatted_business_date = self._format_business_date(business_date)
        except ValueError as e:
            if self.debug_mode:
                print(f"Date formatting error: {e}")
            return None
        
        if self.debug_mode:
            print(f"Using analytics endpoint for business date: {formatted_business_date} (from {business_date})")
        
        # Use the analytics endpoint - timeRange parameter needs clarification
        url = f"{self.api_base_url}/era/v1/metrics/{formatted_business_date}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Toast-Restaurant-External-ID": self.restaurant_guid,
            "Content-Type": "application/json"
        }
        
        # TODO: Need to know what should go in the POST body
        payload = {
            # Add required payload parameters here
        }
        
        try:
            if self.debug_mode:
                print(f"Fetching analytics data from: {url}")
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                if self.debug_mode:
                    print(f"Analytics API Error - Status: {response.status_code}")
                    print(f"Response content: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            
            # Save debug file only if debug mode is enabled
            if self.debug_mode:
                debug_filename = f"debug_analytics_business_date_{formatted_business_date}.json"
                try:
                    with open(debug_filename, 'w') as f:
                        json.dump({
                            'business_date': {
                                'input_date': business_date,
                                'formatted_business_date': formatted_business_date
                            },
                            'analytics_data': data
                        }, f, indent=2)
                    print(f"Debug: Saved analytics data to {debug_filename}")
                except Exception as e:
                    print(f"Warning: Could not save debug file: {e}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            if self.debug_mode:
                print(f"Error retrieving analytics data: {e}")
            return None

    def get_dining_options(self) -> Optional[Dict[str, str]]:
        """Retrieve dining options and create GUID-to-name mapping"""
        if not self._ensure_authenticated():
            if self.debug_mode:
                print("Failed to authenticate for dining options")
            return None
        
        url = f"{self.api_base_url}/config/v2/diningOptions"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Toast-Restaurant-External-ID": self.restaurant_guid,
            "Content-Type": "application/json"
        }
        
        try:
            if self.debug_mode:
                print("Fetching dining option names...")
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                if self.debug_mode:
                    print(f"API Error - Status: {response.status_code}")
                    print(f"Response content: {response.text}")
                return None
            
            response.raise_for_status()
            dining_options = response.json()
            
            # Create GUID-to-name mapping
            dining_option_map = {}
            for option in dining_options:
                guid = option.get('guid')
                name = option.get('name', 'Unknown Option')
                if guid:
                    dining_option_map[guid] = name
            
            if self.debug_mode:
                print(f"Retrieved {len(dining_option_map)} dining option names")
            return dining_option_map
            
        except requests.exceptions.RequestException as e:
            if self.debug_mode:
                print(f"Error retrieving dining options: {e}")
            return None


class SalesSummaryAnalyzer:
    def __init__(self, dining_option_map: Optional[Dict[str, str]] = None):
        self.orders = []
        self.dining_option_map = dining_option_map or {}
    
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
            'discount_breakdown': {},
            'payment_breakdown': {},
            'daily_breakdown': {},
            'order_types': {},
            'dining_options': {},
            'voided_orders': 0,
            'refunded_amount': Decimal('0.00')
        }
        
        # Analyze orders
        for order in orders:
            # Skip None orders
            if order is None:
                continue
            
            order_date = self._extract_date_from_order(order)
            order_type = order.get('source', 'Unknown')
            
            # Initialize daily breakdown
            if order_date not in summary['daily_breakdown']:
                summary['daily_breakdown'][order_date] = {
                    'orders': 0,
                    'gross_sales': Decimal('0.00'),
                    'tips': Decimal('0.00'),
                    'tax': Decimal('0.00'),
                    'discounts': Decimal('0.00')
                }
            
            # Count order types
            summary['order_types'][order_type] = summary['order_types'].get(order_type, 0) + 1
            
            # Track dining options
            dining_option = order.get('diningOption', {}) or {}
            dining_option_guid = dining_option.get('guid', 'Unknown')
            dining_option_name = self.dining_option_map.get(dining_option_guid, dining_option_guid)
            
            if dining_option_guid not in summary['dining_options']:
                summary['dining_options'][dining_option_guid] = {
                    'name': dining_option_name,
                    'count': 0,
                    'gross_sales': Decimal('0.00'),
                    'tips': Decimal('0.00')
                }
            summary['dining_options'][dining_option_guid]['count'] += 1
            
            # Check if order is voided
            if order.get('voided', False):
                summary['voided_orders'] += 1
                continue
            
            # Process each check in the order
            checks = order.get('checks', []) or []
            for check in checks:
                # Skip None checks
                if check is None:
                    continue
                if check.get('voided', False):
                    continue
                
                # Get tax amount from check
                tax_amount = Decimal(str(check.get('taxAmount', 0)))
                summary['total_tax'] += tax_amount
                
                # Initialize check totals
                check_gross_sales = Decimal('0.00')
                check_tips = Decimal('0.00')
                check_discounts = Decimal('0.00')
                
                # Process check-level discounts
                check_discounts += self._process_discounts(check.get('appliedDiscounts', []), summary['discount_breakdown'])
                
                # Process item-level discounts
                for selection in check.get('selections', []):
                    if not selection.get('voided', False):
                        check_discounts += self._process_discounts(selection.get('appliedDiscounts', []), summary['discount_breakdown'])
                        # Also process modifier discounts
                        for modifier in selection.get('modifiers', []):
                            if not modifier.get('voided', False):
                                check_discounts += self._process_discounts(modifier.get('appliedDiscounts', []), summary['discount_breakdown'])
                
                # Process payments for this check
                payments = check.get('payments', []) or []
                for payment in payments:
                    # Skip None payments
                    if payment is None:
                        continue
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
                    
                    
                    summary['total_payments'] += 1
                    
                    # Gross sales = payment amount only (tips are separate)
                    check_gross_sales += payment_amount
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
                summary['total_discounts'] += check_discounts
                
                # Daily breakdown (only count if there were payments)
                if check_gross_sales > 0:
                    summary['daily_breakdown'][order_date]['orders'] += 1
                    summary['daily_breakdown'][order_date]['gross_sales'] += check_gross_sales
                    summary['daily_breakdown'][order_date]['tips'] += check_tips
                    summary['daily_breakdown'][order_date]['tax'] += tax_amount
                    summary['daily_breakdown'][order_date]['discounts'] += check_discounts
                    
                    # Update dining option totals (only count if there were payments)
                    dining_option = order.get('diningOption', {}) or {}
                    dining_option_guid = dining_option.get('guid', 'Unknown')
                    if dining_option_guid in summary['dining_options']:
                        summary['dining_options'][dining_option_guid]['gross_sales'] += check_gross_sales
                        summary['dining_options'][dining_option_guid]['tips'] += check_tips
        
        # Calculate net sales (gross sales - tax - discounts, tips excluded)
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
    
    def _process_discounts(self, applied_discounts: List[Dict], discount_breakdown: Dict) -> Decimal:
        """Process applied discounts and return total discount amount"""
        total_discount = Decimal('0.00')
        
        for discount in applied_discounts:
            if discount.get('voided', False):
                continue
                
            discount_name = discount.get('name', 'Unknown Discount')
            discount_amount = Decimal(str(discount.get('discountAmount', 0)))
            
            # Track discount by type/name
            if discount_name not in discount_breakdown:
                discount_breakdown[discount_name] = {
                    'count': 0,
                    'amount': Decimal('0.00')
                }
            
            discount_breakdown[discount_name]['count'] += 1
            discount_breakdown[discount_name]['amount'] += discount_amount
            total_discount += discount_amount
        
        return total_discount


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




def format_currency(amount: Decimal) -> str:
    """Format decimal amount as currency"""
    return f"${amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"


def display_sales_summary(summary: Dict, start_date: str, end_date: str, show_all: bool = False) -> None:
    """Display formatted sales summary"""
    print(f"\n{'='*80}")
    print(f"SALES SUMMARY: {start_date} to {end_date}")
    print(f"{'='*80}")
    
    # Overall totals (show in all mode)
    if show_all:
        print(f"\n📊 OVERALL TOTALS:")
        print(f"   Total Orders: {summary['total_orders']:,}")
        print(f"   Voided Orders: {summary['voided_orders']:,}")
        print(f"   Gross Sales: {format_currency(summary['gross_sales'])}")
        print(f"   Total Tax: {format_currency(summary['total_tax'])}")
        print(f"   Total Discounts: {format_currency(summary['total_discounts'])}")
        print(f"   Total Tips: {format_currency(summary['total_tips'])}")
        print(f"   Net Sales: {format_currency(summary['net_sales'])}")
    
    # Daily breakdown
    if summary['daily_breakdown']:
        print(f"\n📅 DAILY BREAKDOWN:")
        print(f"   {'Date':<12} {'Orders':<8} {'Gross Sales':<15} {'Discounts':<12} {'Tips':<12} {'Tax':<12}")
        print(f"   {'-'*75}")
        
        # Check if this is a single day report
        is_single_day = start_date == end_date
        
        total_daily_orders = 0
        total_daily_sales = Decimal('0.00')
        total_daily_discounts = Decimal('0.00')
        total_daily_tips = Decimal('0.00')
        total_daily_tax = Decimal('0.00')
        
        for date in sorted(summary['daily_breakdown'].keys()):
            if date != 'Unknown':
                day_data = summary['daily_breakdown'][date]
                orders = day_data['orders']
                sales = day_data['gross_sales']
                discounts = day_data['discounts']
                tips = day_data['tips']
                tax = day_data['tax']
                
                # For single day, skip individual rows and just accumulate totals
                if not is_single_day:
                    print(f"   {date:<12} {orders:<8} {format_currency(sales):<15} {format_currency(discounts):<12} {format_currency(tips):<12} {format_currency(tax):<12}")
                
                total_daily_orders += orders
                total_daily_sales += sales
                total_daily_discounts += discounts
                total_daily_tips += tips
                total_daily_tax += tax
        
        # For single day, show the actual date instead of TOTAL
        if is_single_day:
            print(f"   {start_date:<12} {total_daily_orders:<8} {format_currency(total_daily_sales):<15} {format_currency(total_daily_discounts):<12} {format_currency(total_daily_tips):<12} {format_currency(total_daily_tax):<12}")
        else:
            print(f"   {'-'*75}")
            print(f"   {'TOTAL':<12} {total_daily_orders:<8} {format_currency(total_daily_sales):<15} {format_currency(total_daily_discounts):<12} {format_currency(total_daily_tips):<12} {format_currency(total_daily_tax):<12}")
        
        print(f"   {'-'*75}")
    
    # Payment method breakdown (show in all mode)
    if show_all and summary['payment_breakdown']:
        print(f"\n💳 PAYMENT METHOD BREAKDOWN:")
        print(f"   {'Method':<15} {'Count':<8} {'Amount':<15} {'Tips':<12}")
        print(f"   {'-'*50}")
        
        for method, data in summary['payment_breakdown'].items():
            count = data['count']
            amount = data['amount']
            tips = data['tips']
            print(f"   {method:<15} {count:<8} {format_currency(amount):<15} {format_currency(tips):<12}")
    
    # Discount breakdown (show in all mode)
    if show_all and summary['discount_breakdown']:
        print(f"\n💰 DISCOUNT BREAKDOWN:")
        print(f"   {'Discount Type':<25} {'Count':<8} {'Amount':<15}")
        print(f"   {'-'*48}")
        
        for discount_type, data in summary['discount_breakdown'].items():
            count = data['count']
            amount = data['amount']
            print(f"   {discount_type:<25} {count:<8} {format_currency(amount):<15}")
    
    # Dining option breakdown (show in all mode)
    if show_all and summary['dining_options']:
        print(f"\n🍽️  DINING OPTION BREAKDOWN:")
        print(f"   {'Dining Option':<25} {'Count':<8} {'Gross Sales':<15} {'Tips':<12}")
        print(f"   {'-'*60}")
        
        for dining_option_guid, data in summary['dining_options'].items():
            count = data['count']
            sales = data['gross_sales']
            tips = data['tips']
            # Use human-readable name if available, otherwise show shortened GUID
            display_name = data.get('name', dining_option_guid)
            if display_name == dining_option_guid and len(dining_option_guid) > 25:
                display_name = dining_option_guid[:22] + "..."
            print(f"   {display_name:<25} {count:<8} {format_currency(sales):<15} {format_currency(tips):<12}")
    
    # Order type breakdown (show in all mode)
    if show_all and summary['order_types']:
        print(f"\n📋 ORDER TYPE BREAKDOWN:")
        for order_type, count in summary['order_types'].items():
            percentage = (count / summary['total_orders'] * 100) if summary['total_orders'] > 0 else 0
            print(f"   {order_type}: {count:,} orders ({percentage:.1f}%)")


def display_sales_summary_with_comparison(summary: Dict, start_date: str, end_date: str, 
                                        compare_summary: Dict, compare_start_date: str, compare_end_date: str, 
                                        show_all: bool = False) -> None:
    """Display formatted sales summary with comparison data"""
    print(f"\n{'='*80}")
    print(f"SALES COMPARISON: {start_date} to {end_date} vs {compare_start_date} to {compare_end_date}")
    print(f"{'='*80}")
    
    # Helper function to calculate percentage change
    def percentage_change(current: Decimal, previous: Decimal) -> str:
        if previous == 0:
            return "N/A" if current == 0 else "+∞%"
        change = ((current - previous) / previous) * 100
        sign = "+" if change >= 0 else ""
        return f"{sign}{change:.1f}%"
    
    # Helper function to format change with color indicators
    def format_change(current: Decimal, previous: Decimal) -> str:
        change = current - previous
        pct_change = percentage_change(current, previous)
        sign = "+" if change >= 0 else ""
        return f"{sign}{format_currency(change)} ({pct_change})"
    
    # Key metrics comparison
    print(f"\n📊 KEY METRICS COMPARISON:")
    print(f"   {'Metric':<20} {'Current':<15} {'Previous':<15} {'Change':<20}")
    print(f"   {'-'*70}")
    
    current_gross = summary['gross_sales']
    previous_gross = compare_summary['gross_sales']
    current_tips = summary['total_tips'] 
    previous_tips = compare_summary['total_tips']
    current_orders = summary['total_orders']
    previous_orders = compare_summary['total_orders']
    
    print(f"   {'Gross Sales':<20} {format_currency(current_gross):<15} {format_currency(previous_gross):<15} {format_change(current_gross, previous_gross):<20}")
    print(f"   {'Total Tips':<20} {format_currency(current_tips):<15} {format_currency(previous_tips):<15} {format_change(current_tips, previous_tips):<20}")
    print(f"   {'Total Orders':<20} {current_orders:<15} {previous_orders:<15} {current_orders - previous_orders:+d} ({percentage_change(Decimal(current_orders), Decimal(previous_orders))})    ")
    
    if current_orders > 0 and previous_orders > 0:
        current_avg = current_gross / current_orders
        previous_avg = previous_gross / previous_orders
        print(f"   {'Avg Order Value':<20} {format_currency(current_avg):<15} {format_currency(previous_avg):<15} {format_change(current_avg, previous_avg):<20}")
    
    # Daily breakdown comparison (if both are single days)
    if start_date == end_date and compare_start_date == compare_end_date:
        print(f"\n📅 DAILY BREAKDOWN COMPARISON:")
        print(f"   Current ({start_date}): {current_orders} orders, {format_currency(current_gross)} gross, {format_currency(current_tips)} tips")
        print(f"   Previous ({compare_start_date}): {previous_orders} orders, {format_currency(previous_gross)} gross, {format_currency(previous_tips)} tips")
    
    # Show detailed breakdowns if requested
    if show_all:
        print(f"\n💳 PAYMENT METHOD COMPARISON:")
        if summary['payment_breakdown'] and compare_summary['payment_breakdown']:
            all_methods = set(summary['payment_breakdown'].keys()) | set(compare_summary['payment_breakdown'].keys())
            print(f"   {'Method':<15} {'Current Count':<12} {'Previous Count':<12} {'Current Amount':<15} {'Previous Amount':<15}")
            print(f"   {'-'*80}")
            
            for method in sorted(all_methods):
                curr_data = summary['payment_breakdown'].get(method, {'count': 0, 'amount': Decimal('0.00')})
                prev_data = compare_summary['payment_breakdown'].get(method, {'count': 0, 'amount': Decimal('0.00')})
                
                print(f"   {method:<15} {curr_data['count']:<12} {prev_data['count']:<12} {format_currency(curr_data['amount']):<15} {format_currency(prev_data['amount']):<15}")
        
        # Show individual summaries
        print(f"\n{'='*40} CURRENT PERIOD DETAILS {'='*40}")
        display_sales_summary(summary, start_date, end_date, show_all=True)
        
        print(f"\n{'='*40} COMPARISON PERIOD DETAILS {'='*40}")
        display_sales_summary(compare_summary, compare_start_date, compare_end_date, show_all=True)


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
  python sales.py --today            # Today's sales (display only)
  python sales.py --yesterday --all  # Yesterday's complete report
  python sales.py --date 2025-08-15  # Specific date sales
  python sales.py --today --compare  # Today vs same day last week
  python sales.py --yesterday --compare --all  # Yesterday vs same day last week (detailed)
  python sales.py --date 2025-08-15 --compare  # Aug 15th vs Aug 8th comparison
  python sales.py --this-week        # Current week (Sunday to today)
  python sales.py --last-week        # Complete previous week (Sun-Sat)
  python sales.py --this-month       # Current month (1st to today)
  python sales.py --last-month       # Complete previous month
  python sales.py --this-year        # Current year (Jan 1st to today)
  python sales.py --last-year        # Complete previous year
  python sales.py --range 2025-08-01 2025-08-15  # Custom date range
  python sales.py --today --file my_report.json  # Save to JSON file
        '''
    )
    
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Enable debug mode to save raw API responses to JSON files'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Show complete detailed report (default: only daily breakdown)'
    )
    
    parser.add_argument(
        '--compare',
        action='store_true',
        help='Compare with same day of week from previous week (use with --today, --yesterday, or --date)'
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help='Save results to JSON file with specified filename'
    )
    
    parser.add_argument(
        '--today',
        action='store_true',
        help='Analyze today\'s sales'
    )
    
    parser.add_argument(
        '--yesterday',
        action='store_true',
        help='Analyze yesterday\'s sales'
    )
    
    parser.add_argument(
        '--date',
        type=str,
        metavar='DATE',
        help='Specific date in YYYY-MM-DD format (e.g., --date 2025-08-15)'
    )
    
    parser.add_argument(
        '--range',
        nargs=2,
        metavar=('START', 'END'),
        help='Date range in YYYY-MM-DD format (e.g., --range 2025-08-01 2025-08-15)'
    )
    
    parser.add_argument(
        '--this-month',
        action='store_true',
        help='Analyze current month (1st to today)'
    )
    
    parser.add_argument(
        '--last-month',
        action='store_true',
        help='Analyze complete previous month'
    )
    
    parser.add_argument(
        '--this-year',
        action='store_true',
        help='Analyze current year (Jan 1st to today)'
    )
    
    parser.add_argument(
        '--last-year',
        action='store_true',
        help='Analyze complete previous year'
    )
    
    parser.add_argument(
        '--this-week',
        action='store_true',
        help='Analyze current week (Sunday to today)'
    )
    
    parser.add_argument(
        '--last-week',
        action='store_true',
        help='Analyze complete previous week (Sunday to Saturday)'
    )
    
    return parser.parse_args()


def _get_comparison_date(date_str: str) -> str:
    """Get the same day of week from the previous week"""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    comparison_date = date_obj - timedelta(days=7)
    return str(comparison_date)


def validate_and_get_date_range(args) -> Tuple[str, str, str, str]:
    """Validate arguments and return start_date, end_date, compare_start_date, compare_end_date tuple"""
    today = datetime.now().date()
    
    # Count how many date options are specified
    date_options = sum([
        args.today, 
        args.yesterday, 
        bool(args.date),
        bool(args.range),
        args.this_month,
        args.last_month,
        args.this_year,
        args.last_year,
        args.this_week,
        args.last_week
    ])
    
    # Validate compare option usage
    if args.compare:
        valid_compare_options = args.today or args.yesterday or args.date
        if not valid_compare_options:
            raise ValueError("--compare can only be used with --today, --yesterday, or --date options")
        if args.range or args.this_week or args.last_week or args.this_month or args.last_month or args.this_year or args.last_year:
            raise ValueError("--compare cannot be used with date range options")

    if date_options == 0:
        # Default to today if no date option specified
        return str(today), str(today), None, None
    elif date_options > 1:
        raise ValueError("Please specify only one date option")
    
    if args.today:
        start_date = str(today)
        end_date = str(today)
        if args.compare:
            compare_date = _get_comparison_date(start_date)
            return start_date, end_date, compare_date, compare_date
        return start_date, end_date, None, None
    elif args.yesterday:
        yesterday = today - timedelta(days=1)
        start_date = str(yesterday)
        end_date = str(yesterday)
        if args.compare:
            compare_date = _get_comparison_date(start_date)
            return start_date, end_date, compare_date, compare_date
        return start_date, end_date, None, None
    elif args.date:
        # Validate date format
        try:
            date_dt = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format: {args.date}. Use YYYY-MM-DD format")
        start_date = str(date_dt)
        end_date = str(date_dt)
        if args.compare:
            compare_date = _get_comparison_date(start_date)
            return start_date, end_date, compare_date, compare_date
        return start_date, end_date, None, None
    elif args.range:
        start_date, end_date = args.range
        # Validate date format
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD format")
        
        if end_dt < start_dt:
            raise ValueError("End date must be after or equal to start date")
        
        return start_date, end_date, None, None
    elif args.this_month:
        # Current month from 1st to today
        month_start = today.replace(day=1)
        return str(month_start), str(today), None, None
    elif args.last_month:
        # Complete previous month
        if today.month == 1:
            last_month_start = today.replace(year=today.year-1, month=12, day=1)
            last_month_end = today.replace(day=1) - timedelta(days=1)
        else:
            last_month_start = today.replace(month=today.month-1, day=1)
            # Get last day of previous month
            next_month = today.replace(day=1)
            last_month_end = next_month - timedelta(days=1)
        return str(last_month_start), str(last_month_end), None, None
    elif args.this_year:
        # Current year from Jan 1st to today
        year_start = today.replace(month=1, day=1)
        return str(year_start), str(today), None, None
    elif args.last_year:
        # Complete previous year
        last_year_start = today.replace(year=today.year-1, month=1, day=1)
        last_year_end = today.replace(year=today.year-1, month=12, day=31)
        return str(last_year_start), str(last_year_end), None, None
    elif args.this_week:
        # Current week from Sunday to today
        # Monday=0, Sunday=6 in weekday(), but we want Sunday=0
        days_since_sunday = (today.weekday() + 1) % 7
        this_week_start = today - timedelta(days=days_since_sunday)
        return str(this_week_start), str(today), None, None
    elif args.last_week:
        # Complete previous week (Sunday to Saturday)
        # Calculate this week's Sunday first
        days_since_sunday = (today.weekday() + 1) % 7
        this_week_start = today - timedelta(days=days_since_sunday)
        # Previous week is 7 days before this week
        last_week_start = this_week_start - timedelta(days=7)
        last_week_end = this_week_start - timedelta(days=1)  # Saturday
        return str(last_week_start), str(last_week_end), None, None
    
    # This should never be reached
    return str(today), str(today), None, None


def generate_filename(start_date: str, end_date: str, custom_filename: str = None) -> str:
    """Generate output filename based on date range"""
    if custom_filename:
        if not custom_filename.endswith('.json'):
            custom_filename += '.json'
        return custom_filename
    
    if start_date == end_date:
        return f"sales_summary_business_date_{start_date}.json"
    else:
        return f"sales_summary_{start_date}_to_{end_date}.json"



def main():
    """Main function with command-line interface"""
    # Parse command line arguments
    args = parse_arguments()
    
    try:
        # Validate arguments and get date range
        start_date, end_date, compare_start_date, compare_end_date = validate_and_get_date_range(args)
        
        if args.debug:
            print("Debug mode: Saving raw API responses")
        
        # Load configuration and initialize API client
        if args.debug:
            print("Loading configuration...")
        api_config = load_config()
        if not api_config:
            print("Error: Missing configuration. Please check your .env file.")
            return 1
        
        api_client = ToastSalesAPIClient(
            hostname=api_config['hostname'],
            client_id=api_config['client_id'],
            client_secret=api_config['client_secret'],
            restaurant_guid=api_config['restaurant_guid'],
            debug_mode=args.debug
        )
        
        if args.debug:
            print(f"Connecting to Toast API server: https://{api_client.hostname}")
            print("Testing authentication...")
        if not api_client.authenticate():
            print("Error: Authentication failed. Please check your credentials and hostname.")
            return 1
        
        # Fetch dining option names for human-readable display
        dining_option_map = api_client.get_dining_options()
        if not dining_option_map:
            if args.debug:
                print("Warning: Could not retrieve dining option names. Will show GUIDs instead.")
            dining_option_map = {}
        
        # Fetch sales data
        if args.debug:
            print(f"Fetching sales data from {start_date} to {end_date}...")
        if start_date == end_date:
            orders = api_client.get_orders_by_business_date(start_date)
        else:
            orders = api_client.get_orders_by_date_range(start_date, end_date)
        
        if orders is None:
            print("Error: Failed to retrieve sales data.")
            return 1
        
        # Fetch comparison data if requested
        compare_orders = None
        compare_summary = None
        if compare_start_date and compare_end_date:
            if args.debug:
                print(f"Fetching comparison data from {compare_start_date} to {compare_end_date}...")
            if compare_start_date == compare_end_date:
                compare_orders = api_client.get_orders_by_business_date(compare_start_date)
            else:
                compare_orders = api_client.get_orders_by_date_range(compare_start_date, compare_end_date)
            
            if compare_orders is None:
                print("Warning: Failed to retrieve comparison data. Showing main data only.")
            else:
                if args.debug:
                    print("Analyzing comparison data...")
                compare_analyzer = SalesSummaryAnalyzer(dining_option_map)
                compare_summary = compare_analyzer.analyze_sales_summary(compare_orders)
        
        # Analyze and display results
        if args.debug:
            print("Analyzing sales data...")
        analyzer = SalesSummaryAnalyzer(dining_option_map)
        summary = analyzer.analyze_sales_summary(orders)
        
        # Display results with comparison if available
        if compare_summary:
            display_sales_summary_with_comparison(summary, start_date, end_date, compare_summary, compare_start_date, compare_end_date, args.all)
        else:
            display_sales_summary(summary, start_date, end_date, args.all)
        
        # Save results only if --file is specified
        if args.file:
            filename = generate_filename(start_date, end_date, args.file)
            summary_data = {
                'date_range': {'start': start_date, 'end': end_date},
                'summary': json.loads(json.dumps(summary, default=lambda x: float(x) if isinstance(x, Decimal) else str(x))),
                'raw_orders_count': len(orders),
                'data_source': 'toast_api'
            }
            
            try:
                with open(filename, 'w') as f:
                    json.dump(summary_data, f, indent=2)
                print(f"\nSales summary saved to {filename}")
            except Exception as e:
                print(f"Error saving file: {e}")
                return 1
        
        return 0
        
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
