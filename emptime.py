#!/bin/python3
import requests
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os
from dotenv import load_dotenv
import argparse

class ToastAPIClient:
    def __init__(self, server_name: str, client_id: str, client_secret: str, restaurant_guid: str):
        """
        Initialize Toast API client
        
        Args:
            server_name: Toast server name (e.g., "ws-api.toasttab.com" or "ws-sandbox-api.toasttab.com")
            client_id: Your Toast API client ID
            client_secret: Your Toast API client secret
            restaurant_guid: The GUID of the restaurant
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.restaurant_guid = restaurant_guid
        
        # Clean server name (remove protocol if present)
        if server_name.startswith('https://'):
            self.server_name = server_name.replace('https://', '')
        elif server_name.startswith('http://'):
            self.server_name = server_name.replace('http://', '')
        else:
            self.server_name = server_name
        
        # Set base URLs using cleaned server name
        self.auth_base_url = f"https://{self.server_name}"
        self.api_base_url = f"https://{self.server_name}"
        
        self.access_token = None
        self.token_expires_at = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Toast API and get access token
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        auth_url = f"{self.auth_base_url}/authentication/v1/authentication/login"
        
        headers = {
            "Content-Type": "application/json"
        }
        
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
                # Token typically expires in 1 hour, set expiry time
                self.token_expires_at = datetime.now() + timedelta(minutes=55)
                print("Authentication successful")
                return True
            else:
                print("Authentication failed: No access token received")
                print(f"Response data: {auth_data}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Authentication error: {e}")
            return False
    
    def _ensure_authenticated(self) -> bool:
        """
        Ensure we have a valid access token
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        if not self.access_token or (self.token_expires_at and datetime.now() >= self.token_expires_at):
            return self.authenticate()
        return True
    
    def get_employee_time_logs(self, employee_guid: str, start_date: str, end_date: str, debug: bool = False) -> Optional[List[Dict]]:
        """
        Retrieve time logs for a specific employee within a date range
        
        Args:
            employee_guid: The GUID of the employee
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        
        Returns:
            List of time log entries or None if error
        """
        if not self._ensure_authenticated():
            print("Failed to authenticate")
            return None
        
        # Convert dates to the required format (ISO 8601 in UTC as required by Toast API)
        try:
            # Toast API requires specific format: yyyy-MM-dd'T'HH:mm:ss.SSS-0000
            # Use a broader range to capture PST business days
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Start from beginning of start date PST (which is 8 hours later in UTC)
            start_utc = start_dt + timedelta(hours=8)
            # End at end of end date PST (which is 8 hours + 23:59:59 later in UTC)
            end_utc = end_dt + timedelta(hours=8+23, minutes=59, seconds=59)
            
            # Format exactly as Toast API expects: yyyy-MM-dd'T'HH:mm:ss.SSS-0000
            start_datetime = start_utc.strftime("%Y-%m-%dT%H:%M:%S.000-0000")
            end_datetime = end_utc.strftime("%Y-%m-%dT%H:%M:%S.999-0000")
            
            if debug:
                print(f"DEBUG: API request using Toast format - Start: {start_datetime}, End: {end_datetime}")
                print(f"DEBUG: This represents {start_date} 00:00 PST to {end_date} 23:59 PST")
            
        except ValueError as e:
            print(f"Invalid date format. Please use YYYY-MM-DD format. Error: {e}")
            return None
        
        url = f"{self.api_base_url}/labor/v1/timeEntries"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Toast-Restaurant-External-ID": self.restaurant_guid,
            "Content-Type": "application/json"
        }
        
        # Use startDate and endDate parameters with proper UTC conversion
        params = {
            "startDate": start_datetime,
            "endDate": end_datetime
        }
        
        try:
            if debug:
                print(f"DEBUG: Making API request to: {url}")
                print(f"DEBUG: Parameters: {params}")
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            all_time_logs = response.json()
            if debug:
                print(f"DEBUG: API returned {len(all_time_logs) if isinstance(all_time_logs, list) else 'Not a list'} entries")
            
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving time logs: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            return None
        
        # DEBUG: Print ALL time logs for ALL employees in the date range
        if debug:
            print(f"\n{'='*100}")
            print(f"DEBUG: ALL TIME LOGS FOR DATE RANGE {start_date} to {end_date}")
            print(f"{'='*100}")
            print(f"Total entries returned: {len(all_time_logs) if isinstance(all_time_logs, list) else 'Not a list'}")
            
            if isinstance(all_time_logs, list):
                for i, entry in enumerate(all_time_logs, 1):
                    employee_ref = entry.get('employeeReference', {})
                    entry_employee_guid = employee_ref.get('guid', 'NO-GUID')
                    entry_employee_first = employee_ref.get('firstName', 'Unknown')
                    entry_employee_last = employee_ref.get('lastName', '')
                    
                    in_date_utc = entry.get('inDate', 'N/A')
                    out_date_utc = entry.get('outDate', 'N/A')
                    
                    # Convert UTC to PST for display
                    in_date_pst = convert_utc_to_pst(in_date_utc) if in_date_utc != 'N/A' else 'N/A'
                    out_date_pst = convert_utc_to_pst(out_date_utc) if out_date_utc != 'N/A' else 'N/A'
                    
                    regular_hours = entry.get('regularHours', 0)
                    overtime_hours = entry.get('overtimeHours', 0)
                    total_hours = regular_hours + overtime_hours
                    job_title = entry.get('job', {}).get('title', 'N/A')
                    business_date = entry.get('businessDate', 'N/A')
                    
                    print(f"Entry #{i}:")
                    print(f"  Employee: {entry_employee_first} {entry_employee_last}")
                    print(f"  GUID: {entry_employee_guid}")
                    print(f"  Business Date: {business_date}")
                    print(f"  Clock In (UTC): {in_date_utc}")
                    print(f"  Clock In (PST): {in_date_pst}")
                    print(f"  Clock Out (UTC): {out_date_utc}")
                    print(f"  Clock Out (PST): {out_date_pst}")
                    print(f"  Regular Hours: {regular_hours}")
                    print(f"  Overtime Hours: {overtime_hours}")
                    print(f"  Total Hours: {total_hours}")
                    print(f"  Job: {job_title}")
                    print("-" * 80)
            
            print(f"{'='*100}")
            print(f"END DEBUG - NOW FILTERING FOR EMPLOYEE: {employee_guid}")
            print(f"{'='*100}\n")
        
        # Filter for the specific employee using employeeReference.guid 
        # No need for date filtering since businessDate already handles this
        if isinstance(all_time_logs, list):
            employee_time_logs = []
            matching_entries = 0
            
            for entry in all_time_logs:
                employee_ref = entry.get('employeeReference', {})
                entry_employee_guid = employee_ref.get('guid', '')
                
                # Check if this entry matches our target employee
                if entry_employee_guid == employee_guid:
                    employee_time_logs.append(entry)
                    matching_entries += 1
                    if debug:
                        print(f"FILTERED MATCH #{matching_entries} for {employee_guid}")
            
            if debug:
                print(f"Final filtered result: {matching_entries} entries for employee {employee_guid}")
            return employee_time_logs
        else:
            return all_time_logs if all_time_logs else None
    
    def get_all_employees(self) -> Optional[List[Dict]]:
        """
        Get list of all employees (useful for finding employee GUIDs)
        
        Returns:
            List of employee data or None if error
        """
        if not self._ensure_authenticated():
            print("Failed to authenticate")
            return None
        
        url = f"{self.api_base_url}/labor/v1/employees"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Toast-Restaurant-External-ID": self.restaurant_guid,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            employees = response.json()
            return employees
            
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving employees: {e}")
            return None

def save_employees_to_file(employees: List[Dict], filename: str = "employee.txt") -> None:
    """
    Save employees list to a text file
    
    Args:
        employees: List of employee data
        filename: Name of file to save to
    """
    if not employees:
        print("No employees to save")
        return
    
    try:
        with open(filename, 'w') as f:
            f.write(f"{'='*100}\n")
            f.write(f"{'EMPLOYEE LIST':<100}\n")
            f.write(f"{'='*100}\n")
            f.write(f"{'#':<3} {'Name':<25} {'GUID':<40} {'Email':<30}\n")
            f.write(f"{'-'*100}\n")
            
            for i, emp in enumerate(employees, 1):
                name = f"{emp.get('firstName', '')} {emp.get('lastName', '')}".strip()
                guid = emp.get('guid', 'N/A')
                email = emp.get('email', 'N/A')
                
                f.write(f"{i:<3} {name:<25} {guid:<40} {email:<30}\n")
            
            f.write(f"{'-'*100}\n")
            f.write(f"Total employees: {len(employees)}\n")
        
        print(f"Employee list saved to {filename}")
        print(f"Total employees: {len(employees)}")
        
    except Exception as e:
        print(f"Error saving employee list: {e}")

def load_employee_guids(filename: str = "emp.guids", debug: bool = False) -> List[str]:
    """
    Load employee GUIDs from file
    
    Args:
        filename: Name of file containing GUIDs
        debug: Whether to show debug output
        
    Returns:
        List of employee GUIDs
    """
    try:
        with open(filename, 'r') as f:
            guids = [line.strip() for line in f if line.strip()]
        if debug:
            print(f"Loaded {len(guids)} employee GUIDs from {filename}")
        return guids
    except FileNotFoundError:
        print(f"Error: File {filename} not found")
        return []
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return []

def convert_utc_to_pst(utc_datetime_str: str) -> str:
    """
    Convert UTC datetime string to PST
    
    Args:
        utc_datetime_str: DateTime string in UTC (e.g., "2025-08-02T14:30:00.000-0000")
        
    Returns:
        PST datetime string or original if conversion fails
    """
    try:
        from datetime import timezone, timedelta
        
        # Parse the UTC datetime
        if utc_datetime_str.endswith('-0000'):
            # Remove -0000 and treat as UTC
            dt_str = utc_datetime_str[:-5]
            dt = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
        elif utc_datetime_str.endswith('Z'):
            # Remove Z and treat as UTC
            dt_str = utc_datetime_str[:-1]
            dt = datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc)
        else:
            # Try to parse as ISO format and assume UTC if no timezone
            dt = datetime.fromisoformat(utc_datetime_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        
        # Convert to PST (UTC-8)
        pst = timezone(timedelta(hours=-8))
        pst_dt = dt.astimezone(pst)
        
        return pst_dt.isoformat()
        
    except Exception as e:
        print(f"Warning: Could not convert datetime {utc_datetime_str} to PST: {e}")
        return utc_datetime_str

def is_within_pst_date_range(utc_datetime_str: str, start_date: str, end_date: str) -> bool:
    """
    Check if UTC datetime falls within PST date range
    
    Args:
        utc_datetime_str: UTC datetime string
        start_date: Start date in YYYY-MM-DD (PST)
        end_date: End date in YYYY-MM-DD (PST)
        
    Returns:
        True if within range, False otherwise
    """
    try:
        pst_datetime_str = convert_utc_to_pst(utc_datetime_str)
        pst_date = pst_datetime_str.split('T')[0]  # Extract date part
        
        return start_date <= pst_date <= end_date
    except:
        return True  # Include if we can't determine

def get_previous_week_dates() -> tuple:
    """
    Get the previous week's Sunday to Saturday date range
    
    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    today = datetime.now()
    
    # Find the previous Sunday (0 = Monday, 6 = Sunday)
    days_since_sunday = (today.weekday() + 1) % 7
    last_sunday = today - timedelta(days=days_since_sunday + 7)  # Go back one more week
    
    # Following Saturday is 6 days after Sunday
    following_saturday = last_sunday + timedelta(days=6)
    
    start_date = last_sunday.strftime("%Y-%m-%d")
    end_date = following_saturday.strftime("%Y-%m-%d")
    
    return start_date, end_date
    """
    Get the previous week's Sunday to Saturday date range
    
    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    today = datetime.now()
    
    # Find the previous Sunday (0 = Monday, 6 = Sunday)
    days_since_sunday = (today.weekday() + 1) % 7
    last_sunday = today - timedelta(days=days_since_sunday + 7)  # Go back one more week
    
    # Following Saturday is 6 days after Sunday
    following_saturday = last_sunday + timedelta(days=6)
    
    start_date = last_sunday.strftime("%Y-%m-%d")
    end_date = following_saturday.strftime("%Y-%m-%d")
    
    return start_date, end_date

def validate_date(date_string: str) -> bool:
    """
    Validate date format
    
    Args:
        date_string: Date in YYYY-MM-DD format
        
    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def format_employee_summary(employee_name: str, time_logs: List[Dict]) -> None:
    """
    Format and display summary for a single employee
    
    Args:
        employee_name: Name of the employee
        time_logs: List of time log entries for this employee
    """
    if not time_logs:
        print(f"{employee_name}: No time logs found")
        return
    
    total_regular_hours = 0.0
    total_overtime_hours = 0.0
    
    for entry in time_logs:
        total_regular_hours += entry.get('regularHours', 0)
        total_overtime_hours += entry.get('overtimeHours', 0)
    
    total_hours = total_regular_hours + total_overtime_hours
    
    print(f"{employee_name}:")
    print(f"  Regular Hours: {total_regular_hours:.2f}")
    print(f"  Overtime Hours: {total_overtime_hours:.2f}")
    print(f"  Total Hours: {total_hours:.2f}")
    print(f"  Entries: {len(time_logs)}")
    print()

def get_employee_name_by_guid(client: ToastAPIClient, employee_guid: str) -> str:
    """
    Get employee name by matching GUID from the employee list
    
    Args:
        client: ToastAPIClient instance
        employee_guid: The GUID to look up
        
    Returns:
        Employee name or 'Unknown Employee'
    """
    employees = client.get_all_employees()
    if not employees:
        return "Unknown Employee"
    
    for emp in employees:
        if emp.get('guid') == employee_guid:
            first_name = emp.get('firstName', '')
            last_name = emp.get('lastName', '')
            return f"{first_name} {last_name}".strip()
    
    return "Unknown Employee"

def load_config() -> Dict[str, str]:
    """
    Load configuration from .env file
    
    Returns:
        Dictionary with configuration values
    """
    load_dotenv()
    
    config = {
        'server_name': os.getenv('TOAST_HOSTNAME'),
        'client_id': os.getenv('TOAST_CLIENT_ID'),
        'client_secret': os.getenv('TOAST_CLIENT_SECRET'),
        'restaurant_guid': os.getenv('TOAST_RESTAURANT_GUID')
    }
    
    # Check if all required values are present
    missing_values = [key for key, value in config.items() if not value]
    if missing_values:
        print(f"Error: Missing required environment variables: {', '.join(missing_values)}")
        print("\nPlease create a .env file with the following variables:")
        print("TOAST_HOSTNAME=ws-sandbox-api.toasttab.com")
        print("TOAST_CLIENT_ID=your_client_id")
        print("TOAST_CLIENT_SECRET=your_client_secret")
        print("TOAST_RESTAURANT_GUID=your_restaurant_guid")
        print("\nNote: Server name should NOT include 'https://' - just the hostname")
        return None
    
    return config

def main():
    """
    Main function with command-line interface
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Toast API Time Logs Manager')
    parser.add_argument('-t', '--time-logs', action='store_true', 
                       help='Get time logs for employees (uses previous week: Sunday to Saturday)')
    parser.add_argument('-s', '--start', type=str, 
                       help='Start date (YYYY-MM-DD) - must be used with -e')
    parser.add_argument('-e', '--end', type=str, 
                       help='End date (YYYY-MM-DD) - must be used with -s')
    parser.add_argument('-d', '--debug', action='store_true', 
                       help='Enable debug output showing detailed API responses')
    args = parser.parse_args()
    
    # Validate date arguments
    if (args.start and not args.end) or (args.end and not args.start):
        print("Error: Both -s (start) and -e (end) must be specified together")
        return
    
    if args.start and args.end:
        if not validate_date(args.start):
            print(f"Error: Invalid start date format '{args.start}'. Use YYYY-MM-DD")
            return
        if not validate_date(args.end):
            print(f"Error: Invalid end date format '{args.end}'. Use YYYY-MM-DD")
            return
        if datetime.strptime(args.end, "%Y-%m-%d") < datetime.strptime(args.start, "%Y-%m-%d"):
            print("Error: End date must be after start date")
            return
    
    # Load configuration from .env file
    config = load_config()
    if not config:
        return
    
    # Initialize client
    client = ToastAPIClient(
        server_name=config['server_name'],
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        restaurant_guid=config['restaurant_guid']
    )
    
    print(f"Connecting to Toast API server: https://{client.server_name}")
    
    # Test authentication
    print("Testing authentication...")
    if not client.authenticate():
        print("Authentication failed. Please check your credentials and server name.")
        return
    
    if args.time_logs or (args.start and args.end):
        # Time logs mode
        employee_guids = load_employee_guids("emp.guids", args.debug)
        if not employee_guids:
            print("No employee GUIDs found. Please create emp.guids file with one GUID per line.")
            return
        
        # Determine date range
        if args.start and args.end:
            start_date = args.start
            end_date = args.end
            print(f"Using custom date range: {start_date} to {end_date}")
        else:
            start_date, end_date = get_previous_week_dates()
            print(f"Using previous week: {start_date} (Sunday) to {end_date} (Saturday)")
        
        # Process each employee
        all_time_logs = []
        grand_total_regular = 0.0
        grand_total_overtime = 0.0
        
        print(f"\n{'='*60}")
        print(f"TIME LOG SUMMARY ({start_date} to {end_date})")
        print(f"{'='*60}")
        
        for guid in employee_guids:
            time_logs = client.get_employee_time_logs(guid, start_date, end_date, args.debug)
            
            if time_logs:
                # Get employee name by matching GUID from employee list
                employee_name = get_employee_name_by_guid(client, guid)
                
                # Display summary for this employee
                format_employee_summary(employee_name, time_logs)
                
                # Add to combined data for JSON export
                all_time_logs.extend(time_logs)
                
                # Add to grand totals
                for entry in time_logs:
                    grand_total_regular += entry.get('regularHours', 0)
                    grand_total_overtime += entry.get('overtimeHours', 0)
            else:
                # Still get the name even if no time logs found
                employee_name = get_employee_name_by_guid(client, guid)
                print(f"{employee_name} (GUID: {guid}): No time logs found")
                print()
        
        # Display grand totals only in debug mode
        if args.debug:
            grand_total_hours = grand_total_regular + grand_total_overtime
            print(f"{'='*60}")
            print(f"GRAND TOTALS FOR ALL EMPLOYEES:")
            print(f"{'='*60}")
            print(f"Total Regular Hours: {grand_total_regular:.2f}")
            print(f"Total Overtime Hours: {grand_total_overtime:.2f}")
            print(f"TOTAL HOURS: {grand_total_hours:.2f}")
            processed_count = len([g for g in employee_guids if client.get_employee_time_logs(g, start_date, end_date, args.debug)])
            print(f"Total Employees Processed: {processed_count}")
            print(f"{'='*60}")
        
        # Save detailed data to JSON file
        if all_time_logs:
            filename = f"time_logs_detailed_{start_date}_to_{end_date}.json"
            try:
                with open(filename, 'w') as f:
                    json.dump(all_time_logs, f, indent=2)
                print(f"\nDetailed time log entries saved to {filename}")
                print(f"Total detailed entries: {len(all_time_logs)}")
            except Exception as e:
                print(f"Error saving detailed file: {e}")
        else:
            print("No time logs found for any of the specified employees.")
    
    else:
        # Default mode: get employee list and save to employee.txt
        print("Fetching employees...")
        employees = client.get_all_employees()
        
        if employees:
            save_employees_to_file(employees, "employee.txt")
        else:
            print("Failed to retrieve employees or no employees found.")

if __name__ == "__main__":
    main()
