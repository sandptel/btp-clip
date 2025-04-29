import os.path
import json

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
        
        # Read data from the sheet
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