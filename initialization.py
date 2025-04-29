import os
import json
import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define global variables
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")
SHEETS_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "sheets.json")

# Global variables for spreadsheet operations
spreadsheet_id = None
sheets_service = None


def get_credentials():
    """Get valid credentials for Google Sheets API."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_info(
            json.loads(open(TOKEN_FILE).read()), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    
    return creds


def load_spreadsheet_id():
    """Load spreadsheet ID from sheets.json if it exists."""
    global spreadsheet_id
    if os.path.exists(SHEETS_CONFIG_FILE):
        with open(SHEETS_CONFIG_FILE, "r") as f:
            config = json.load(f)
            spreadsheet_id = config.get("spreadsheet_id")
    return spreadsheet_id


def save_spreadsheet_id():
    """Save spreadsheet ID to sheets.json."""
    global spreadsheet_id
    with open(SHEETS_CONFIG_FILE, "w") as f:
        json.dump({"spreadsheet_id": spreadsheet_id}, f)


def create_new_spreadsheet():
    """Create a new Google Sheet and return its ID."""
    global spreadsheet_id, sheets_service
    
    spreadsheet = {
        'properties': {
            'title': 'Clipboard History'
        },
        'sheets': [{
            'properties': {
                'title': 'Sheet1'
            }
        }]
    }
    
    try:
        spreadsheet_result = sheets_service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = spreadsheet_result.get('spreadsheetId')
        print(f"Created new spreadsheet with ID: {spreadsheet_id}")
        save_spreadsheet_id()
        return spreadsheet_id
    except HttpError as err:
        print(f"An error occurred while creating spreadsheet: {err}")
        raise


def initialize_sheets_service():
    """Initialize the Google Sheets service."""
    global sheets_service
    
    creds = get_credentials()
    sheets_service = build("sheets", "v4", credentials=creds)
    
    return sheets_service


def check_and_reset_sheet():
    """
    Checks if the header row contains expected values and resets the sheet if not.
    Expected values: A1="clipboard", B1="date-time", C1="system info"
    """
    global spreadsheet_id, sheets_service
    
    try:
        # Check if the spreadsheet exists, if not create it
        if not spreadsheet_id:
            load_spreadsheet_id()
            
        if not spreadsheet_id:
            create_new_spreadsheet()
            
        try:
            # Try to get spreadsheet info to check if it exists
            sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        except HttpError as err:
            if err.resp.status == 404:
                # Spreadsheet doesn't exist, create a new one
                print("Spreadsheet not found. Creating a new spreadsheet...")
                create_new_spreadsheet()
            else:
                raise  # Re-raise if it's not a 404 error

        # Now read the first row to check headers
        range_name = "Sheet1!A1:C1"
        
        try:
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_name).execute()
            values = result.get('values', [])
        except HttpError:
            # If there's any error, assume we need to reset
            values = []
        
        # Check if the first row contains expected headers
        needs_reset = False
        
        if not values:
            # No data exists, needs reset
            needs_reset = True
        else:
            first_row = values[0]
            # Check A1 for "clipboard"
            if len(first_row) < 1 or first_row[0].lower() != "clipboard":
                needs_reset = True
            # Check B1 for "date-time"  
            if len(first_row) < 2 or first_row[1].lower() != "date-time":
                needs_reset = True
            # Check C1 for "system info"
            if len(first_row) < 3 or first_row[2].lower() != "system":
                needs_reset = True
        
        if needs_reset:
            print("Header row is not correctly set up. Resetting sheet...")
            
            # Clear all data from the sheet
            try:
                clear_range = "Sheet1"
                sheets_service.spreadsheets().values().clear(
                    spreadsheetId=spreadsheet_id, range=clear_range,
                    body={}).execute()
            except HttpError:
                # If clear fails, we'll overwrite headers anyway
                pass
            
            # Write header row with expected values
            body = {
                'values': [['clipboard', 'date-time', 'system']]
            }
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range="Sheet1!A1:C1",
                valueInputOption="RAW", body=body).execute()
            
            print("Sheet has been reset with proper headers.")
            return True  # Sheet was reset
        else:
            print("Sheet headers are correctly set up.")
            return False  # Sheet was not reset
            
    except HttpError as err:
        print(f"An error occurred while checking/resetting sheet: {err}")
        raise


def update_clipboard(clipboard_content):
    """
    Adds new clipboard content in column A below the header row.
    """
    global spreadsheet_id, sheets_service
    
    try:
        # First, find the first empty row in column A
        range_name = "Sheet1!A:A"
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        
        # Start at row 2 (after header) if values exist, otherwise start at row 2 anyway
        next_row = len(values) + 1 if values else 2
        
        # Update the cell in column A
        body = {
            'values': [[clipboard_content]]
        }
        update_range = f"Sheet1!A{next_row}"
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=update_range,
            valueInputOption="RAW", body=body).execute()
        
        print(f"Added clipboard content at A{next_row}")
        return next_row
        
    except HttpError as err:
        print(f"An error occurred while updating clipboard content: {err}")
        raise


def update_datetime(datetime_value, row=None):
    """
    Adds datetime value in column B at the specified row or the first empty row.
    """
    global spreadsheet_id, sheets_service
    
    try:
        if row is None:
            # Find the first empty row in column B
            range_name = "Sheet1!B:B"
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_name).execute()
            values = result.get('values', [])
            
            # Start at row 2 (after header) if values exist, otherwise start at row 2 anyway
            row = len(values) + 1 if values else 2
        
        # Update the cell in column B
        body = {
            'values': [[datetime_value]]
        }
        update_range = f"Sheet1!B{row}"
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=update_range,
            valueInputOption="RAW", body=body).execute()
        
        print(f"Added date-time at B{row}")
        
    except HttpError as err:
        print(f"An error occurred while updating date-time: {err}")
        raise


def update_sysinfo(system_info, row=None):
    """
    Adds system information in column C at the specified row or the first empty row.
    """
    global spreadsheet_id, sheets_service
    
    try:
        if row is None:
            # Find the first empty row in column C
            range_name = "Sheet1!C:C"
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_name).execute()
            values = result.get('values', [])
            
            # Start at row 2 (after header) if values exist, otherwise start at row 2 anyway
            row = len(values) + 1 if values else 2
        
        # Update the cell in column C
        body = {
            'values': [[system_info]]
        }
        update_range = f"Sheet1!C{row}"
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=update_range,
            valueInputOption="RAW", body=body).execute()
        
        print(f"Added system info at C{row}")
        
    except HttpError as err:
        print(f"An error occurred while updating system info: {err}")
        raise


def add_clipboard_entry(clipboard_content, datetime_value=None, system_info=None):
    """
    Adds a complete clipboard entry with all associated data across columns A, B, and C.
    """
    try:
        # Set default values if not provided
        if datetime_value is None:
            from datetime import datetime
            datetime_value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        if system_info is None:
            import socket
            system_info = socket.gethostname()
        
        # Add clipboard content and get the row
        row = update_clipboard(clipboard_content)
        
        # Add date-time and system info to the same row
        update_datetime(datetime_value, row)
        update_sysinfo(system_info, row)
        
        print(f"Added complete clipboard entry at row {row}")
        
    except Exception as e:
        print(f"An error occurred while adding clipboard entry: {e}")
        raise


def main():
    """Connect to Google Sheets API and manage clipboard data."""
    global sheets_service, spreadsheet_id
    
    try:
        # Initialize sheets service
        sheets_service = initialize_sheets_service()
        
        # Load or create spreadsheet
        spreadsheet_id = load_spreadsheet_id()
        
        # Check and reset the sheet if needed
        check_and_reset_sheet()
        
        # Example usage
        add_clipboard_entry("Example clipboard content")
        
    except HttpError as err:
        print(f"An error occurred: {err}")


if __name__ == "__main__":
    main()