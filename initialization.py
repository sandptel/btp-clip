import os.path
import json
import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
# Changed to allow full access to sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# JSON file to store the spreadsheet ID
SHEETS_CONFIG_FILE = "sheets.json"
DEFAULT_RANGE_NAME = "Sheet1!A1:Z"


def get_credentials():
    """Get and return the credentials needed to access the Google Sheets API."""
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_info(
            json.loads(open("token.json").read()), SCOPES
        )
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def load_spreadsheet_id():
    """Load spreadsheet ID from sheets.json if it exists."""
    if os.path.exists(SHEETS_CONFIG_FILE):
        with open(SHEETS_CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config.get("spreadsheet_id")
    return None


def save_spreadsheet_id(spreadsheet_id):
    """Save spreadsheet ID to sheets.json."""
    with open(SHEETS_CONFIG_FILE, "w") as f:
        json.dump({"spreadsheet_id": spreadsheet_id}, f)


def create_new_spreadsheet(service):
    """Create a new Google Sheet and return its ID."""
    spreadsheet = {
        'properties': {
            'title': 'BTP-2 Data Sheet'
        }
    }
    
    spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
    spreadsheet_id = spreadsheet.get('spreadsheetId')
    
    print(f"Created new spreadsheet with ID: {spreadsheet_id}")
    return spreadsheet_id


def check_and_reset_sheet(service, spreadsheet_id):
    """
    Checks if the header row contains expected values and resets the sheet if not.
    Expected values: A1="clipboard", B1="date-time", C1="system info"
    
    Args:
        service: Authenticated Google Sheets service object
        spreadsheet_id: ID of the spreadsheet to check and reset
    """
    try:
        # Check if the spreadsheet exists, if not create it
        try:
            # Try to get spreadsheet info to check if it exists
            service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        except HttpError as err:
            if err.resp.status == 404:
                # Spreadsheet doesn't exist, create a new one
                print("Spreadsheet not found. Creating a new spreadsheet...")
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
                spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
                spreadsheet_id = spreadsheet.get('spreadsheetId')
                print(f"Created new spreadsheet with ID: {spreadsheet_id}")
            else:
                raise  # Re-raise if it's not a 404 error

        # Now read the first row to check headers
        range_name = "Sheet1!A1:C1"
        
        try:
            result = service.spreadsheets().values().get(
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
            if len(first_row) < 3 or first_row[2].lower() != "system info":
                needs_reset = True
        
        if needs_reset:
            print("Header row is not correctly set up. Resetting sheet...")
            
            # Clear all data from the sheet
            try:
                clear_range = "Sheet1"
                service.spreadsheets().values().clear(
                    spreadsheetId=spreadsheet_id, range=clear_range,
                    body={}).execute()
            except HttpError:
                # If clear fails, we'll overwrite headers anyway
                pass
            
            # Write header row with expected values
            body = {
                'values': [['clipboard', 'date-time', 'system info']]
            }
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range="Sheet1!A1:C1",
                valueInputOption="RAW", body=body).execute()
            
            print("Sheet has been reset with proper headers.")
            return spreadsheet_id, True  # Return the ID and reset status
        else:
            print("Sheet headers are correctly set up.")
            return spreadsheet_id, False  # Return the ID and reset status
            
    except HttpError as err:
        print(f"An error occurred while checking/resetting sheet: {err}")
        raise


def update_clipboard(service, spreadsheet_id, clipboard_content):
    """
    Adds new clipboard content in column A below the header row.
    
    Args:
        service: Authenticated Google Sheets service object
        spreadsheet_id: ID of the spreadsheet
        clipboard_content: Text content to add to the clipboard column
    """
    try:
        # First, find the first empty row in column A
        range_name = "Sheet1!A:A"
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        
        # Start at row 2 (after header) if values exist, otherwise start at row 2 anyway
        next_row = len(values) + 1 if values else 2
        
        # Update the cell in column A
        body = {
            'values': [[clipboard_content]]
        }
        update_range = f"Sheet1!A{next_row}"
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=update_range,
            valueInputOption="RAW", body=body).execute()
        
        print(f"Added clipboard content at A{next_row}")
        return next_row
        
    except HttpError as err:
        print(f"An error occurred while updating clipboard content: {err}")
        raise


def update_datetime(service, spreadsheet_id, datetime_value, row=None):
    """
    Adds datetime value in column B at the specified row or the first empty row.
    
    Args:
        service: Authenticated Google Sheets service object
        spreadsheet_id: ID of the spreadsheet
        datetime_value: Date-time value to add
        row: Optional row number to update. If None, adds to the first empty row.
    """
    try:
        if row is None:
            # Find the first empty row in column B
            range_name = "Sheet1!B:B"
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_name).execute()
            values = result.get('values', [])
            
            # Start at row 2 (after header) if values exist, otherwise start at row 2 anyway
            row = len(values) + 1 if values else 2
        
        # Update the cell in column B
        body = {
            'values': [[datetime_value]]
        }
        update_range = f"Sheet1!B{row}"
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=update_range,
            valueInputOption="RAW", body=body).execute()
        
        print(f"Added date-time at B{row}")
        
    except HttpError as err:
        print(f"An error occurred while updating date-time: {err}")
        raise


def update_sysinfo(service, spreadsheet_id, system_info, row=None):
    """
    Adds system information in column C at the specified row or the first empty row.
    
    Args:
        service: Authenticated Google Sheets service object
        spreadsheet_id: ID of the spreadsheet
        system_info: System information to add
        row: Optional row number to update. If None, adds to the first empty row.
    """
    try:
        if row is None:
            # Find the first empty row in column C
            range_name = "Sheet1!C:C"
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_name).execute()
            values = result.get('values', [])
            
            # Start at row 2 (after header) if values exist, otherwise start at row 2 anyway
            row = len(values) + 1 if values else 2
        
        # Update the cell in column C
        body = {
            'values': [[system_info]]
        }
        update_range = f"Sheet1!C{row}"
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=update_range,
            valueInputOption="RAW", body=body).execute()
        
        print(f"Added system info at C{row}")
        
    except HttpError as err:
        print(f"An error occurred while updating system info: {err}")
        raise


def add_clipboard_entry(service, spreadsheet_id, clipboard_content, datetime_value=None, system_info=None):
    """
    Adds a complete clipboard entry with all associated data across columns A, B, and C.
    
    Args:
        service: Authenticated Google Sheets service object
        spreadsheet_id: ID of the spreadsheet
        clipboard_content: Text content to add to the clipboard column
        datetime_value: Optional date-time value (defaults to current time if None)
        system_info: Optional system information (defaults to current hostname if None)
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
        row = update_clipboard(service, spreadsheet_id, clipboard_content)
        
        # Add date-time and system info to the same row
        update_datetime(service, spreadsheet_id, datetime_value, row)
        update_sysinfo(service, spreadsheet_id, system_info, row)
        
        print(f"Added complete clipboard entry at row {row}")
        
    except Exception as e:
        print(f"An error occurred while adding clipboard entry: {e}")
        raise


def main():
    """Connect to Google Sheets API and read/create a spreadsheet."""
    try:
        creds = get_credentials()
        service = build("sheets", "v4", credentials=creds)
        
        # Get the spreadsheet ID from sheets.json or create a new one
        spreadsheet_id = load_spreadsheet_id()
        if not spreadsheet_id:
            spreadsheet_id = create_new_spreadsheet(service)
            save_spreadsheet_id(spreadsheet_id)
        
        # Call the updated function to check and reset if needed
        spreadsheet_id, was_reset = check_and_reset_sheet(service, spreadsheet_id)
        
        # Example usage of add_clipboard
        # Uncomment to test:
        update_clipboard(service, spreadsheet_id, "hello world")
        update_datetime(service, spreadsheet_id, "2023-10-01 12:00:00")
        update_sysinfo(service, spreadsheet_id, "System Info Example")
        
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                    range=DEFAULT_RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            print("No data found.")
            return

        print("Data from spreadsheet:")
        for row in values:
            print(row)
            
    except HttpError as err:
        print(f"An error occurred: {err}")


if __name__ == "__main__":
    main()