#!/usr/bin/env python3

import os
import sys
import socket
import platform
from datetime import datetime
import pyperclip  # For clipboard operations

# Import functions from initialization.py
from initialization import (
    initialize_sheets_service,
    load_spreadsheet_id,
    check_and_reset_sheet,
    add_clipboard_entry
)

def get_clipboard_content():
    """Get current clipboard content."""
    try:
        clipboard_content = pyperclip.paste()
        return clipboard_content
    except Exception as e:
        print(f"Error getting clipboard content: {e}")
        return f"Error accessing clipboard: {str(e)}"

def get_system_info():
    """Get current system hostname as identifier."""
    try:
        return socket.gethostname()
    except Exception as e:
        print(f"Error getting system info: {e}")
        return "unknown-system"

def get_latest_cloud_clipboard():
    """
    Get the latest clipboard content from Google Sheets.
    
    Returns:
        tuple: (content, system_id, timestamp) - The latest clipboard content, 
               the system that updated it, and when it was updated
    """
    try:
        # Initialize sheets service
        sheets_service = initialize_sheets_service()
        
        # Load spreadsheet ID
        spreadsheet_id = load_spreadsheet_id()
        
        if not sheets_service or not spreadsheet_id:
            print("Failed to initialize Google Sheets service or load spreadsheet ID")
            return "", "", ""
        
        # Get the data from the sheet
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A:C"
        ).execute()
        
        values = result.get('values', [])
        
        if not values or len(values) <= 1:  # Only header row or no data
            print("No data found in clipboard history.")
            return "", "", ""
        
        # Get the most recent entry (last row)
        last_row = values[-1]
        
        # Extract content and metadata (based on our sheet structure)
        content = last_row[0] if len(last_row) > 0 else ""
        timestamp = last_row[1] if len(last_row) > 1 else ""
        system_id = last_row[2] if len(last_row) > 2 else ""
        
        print(f"Found latest clipboard entry from system {system_id}")
        return content, system_id, timestamp
        
    except Exception as e:
        print(f"Error retrieving cloud clipboard: {e}")
        return "", "", ""

def push_clipboard():
    """
    Push the local clipboard content to Google Sheets.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Initialize services
        initialize_sheets_service()
        load_spreadsheet_id()
        check_and_reset_sheet()
        
        # Get local clipboard content
        content = get_clipboard_content()
        if not content or content.startswith("Error accessing clipboard"):
            print("No valid clipboard content to push.")
            return False
            
        # Get system info
        system_info = get_system_info()
        
        # Get current datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add entry to Google Sheet
        add_clipboard_entry(content, now, system_info)
        
        print(f"Pushed clipboard content to cloud. Length: {len(content)} characters")
        return True
        
    except Exception as e:
        print(f"Error pushing clipboard to cloud: {e}")
        return False

def pull_clipboard():
    """
    Pull the latest clipboard content from Google Sheets and update local clipboard 
    only if the content comes from a different system.
    
    Returns:
        bool: True if local clipboard was updated, False otherwise
    """
    try:
        # Initialize services
        initialize_sheets_service()
        load_spreadsheet_id()
        
        # Get the latest clipboard content from the cloud
        content, source_system, timestamp = get_latest_cloud_clipboard()
        
        if not content:
            print("No clipboard content found in cloud.")
            return False
        
        # Get the current system's ID
        current_system_id = get_system_info()
        
        # Only update local clipboard if content is from a different system
        if source_system == current_system_id:
            print(f"Latest cloud clipboard content is from this system ({current_system_id}).")
            print("No need to update local clipboard.")
            return False
        
        # Update the local system clipboard with content from another system
        pyperclip.copy(content)
        print(f"Local clipboard updated with content from system '{source_system}'")
        print(f"Content length: {len(content)} characters")
        print(f"Content timestamp: {timestamp}")
        return True
        
    except Exception as e:
        print(f"Error pulling clipboard from cloud: {e}")
        return False

def print_debug_info():
    """Print debug information about the environment."""
    print("\n=== DEBUG INFO ===")
    try:
        print(f"Python version: {platform.python_version()}")
        print(f"System: {platform.system()} {platform.version()}")
        print(f"Machine: {platform.machine()}")
        print(f"Hostname: {socket.gethostname()}")
        
        # Try to check clipboard access
        clipboard_test = pyperclip.paste()
        print(f"Debug - Clipboard accessible: {bool(clipboard_test is not None)}")
        print(f"Debug - Clipboard content length: {len(clipboard_test) if clipboard_test else 0}")
    except Exception as debug_err:
        print(f"Error collecting debug info: {debug_err}")

def main():
    """
    Main function for clipboard synchronization.
    """
    try:
        # Parse command line arguments
        import argparse
        
        parser = argparse.ArgumentParser(description='Clipboard Cloud Sync')
        parser.add_argument('--pull', action='store_true', help='Pull clipboard from cloud to local system')
        parser.add_argument('--push', action='store_true', help='Push local clipboard to cloud')
        parser.add_argument('--debug', action='store_true', help='Print debug information')
        
        args = parser.parse_args()
        
        if args.push:
            push_clipboard()
        elif args.pull:
            pull_clipboard()
        elif args.debug:
            print_debug_info()
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error in main function: {e}")
        print_debug_info()
        sys.exit(1)

if __name__ == "__main__":
    main()