#!/usr/bin/env python3

import os
import sys
import socket
import platform
from datetime import datetime
import subprocess
import pyperclip  # You may need to install this: pip install pyperclip

# Import functions from initialization.py
from initialization import (
    initialize_sheets_service,
    load_spreadsheet_id,
    check_and_reset_sheet,
    add_clipboard_entry,
    update_clipboard,
    update_datetime,
    update_sysinfo
)

def get_system_info():
    """
    Collect system information including hostname, platform, user, etc.
    
    Returns:
        str: Formatted system information
    """
    try:
        hostname = socket.gethostname()
        platform_info = platform.platform()
        username = os.getlogin()
        
        # Get active window/application name (Linux-specific)
        active_window = "Unknown"
        try:
            if sys.platform.startswith('linux'):
                # Use xdotool to get the active window name
                cmd = "xdotool getwindowfocus getwindowname"
                active_window = subprocess.check_output(cmd, shell=True).decode().strip()
            elif sys.platform == 'darwin':  # macOS
                cmd = "osascript -e 'tell application \"System Events\" to get name of first application process whose frontmost is true'"
                active_window = subprocess.check_output(cmd, shell=True).decode().strip()
            elif sys.platform == 'win32':  # Windows
                # This requires additional libraries like pywin32
                import win32gui
                active_window = win32gui.GetWindowText(win32gui.GetForegroundWindow())
        except Exception as e:
            print(f"Failed to get active window: {e}")
            active_window = "Error detecting window"
        
        # Format the system information
        sys_info = f"Host: {hostname} | OS: {platform_info} | User: {username}"
        return sys_info
    except Exception as e:
        print(f"Error getting system information: {e}")
        return f"Error: {str(e)}"
    
def get_clipboard_content():
    """
    Get the current clipboard content.
    
    Returns:
        str: Current clipboard content
    """
    try:
        clipboard_content = pyperclip.paste()
        # Truncate if too long (Google Sheets has limits on cell content)
        if len(clipboard_content) > 50000:
            clipboard_content = clipboard_content[:50000] + "... (content truncated)"
        return clipboard_content
    except Exception as e:
        print(f"Error getting clipboard content: {e}")
        return f"Error accessing clipboard: {str(e)}"

def get_latest_cloud_clipboard():
    """
    Get the latest clipboard content from Google Sheets.
    
    Returns:
        tuple: (content, system_id, timestamp) - The latest clipboard content, 
               the system that updated it, and when it was updated
    """
    try:
        # Make sure service is initialized
        if not initialization.sheets_service:
            initialization.initialize_sheets_service()
        
        # Make sure spreadsheet ID is loaded
        if not initialization.spreadsheet_id:
            initialization.load_spreadsheet_id()
        
        # Get the data from the sheet
        result = initialization.sheets_service.spreadsheets().values().get(
            spreadsheetId=initialization.spreadsheet_id,
            range="Sheet1!A:C"
        ).execute()
        
        values = result.get('values', [])
        
        if not values or len(values) <= 1:  # Only header row or no data
            print("No data found in clipboard history.")
            return "", "", ""
        
        # Get the most recent entry (last row)
        last_row = values[-1]
        
        # Extract content and metadata
        content = last_row[0] if len(last_row) > 0 else ""
        timestamp = last_row[1] if len(last_row) > 1 else ""
        system_id = last_row[2] if len(last_row) > 2 else ""
        
        print(f"Found latest clipboard entry from system {system_id}")
        return content, system_id, timestamp
        
    except Exception as e:
        print(f"Error retrieving cloud clipboard: {e}")
        return "", "", ""

def sync_from_cloud_to_local():
    """
    Get the latest clipboard content from Google Sheets and update the system clipboard.
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Initialize services
        initialization.initialize_sheets_service()
        initialization.load_spreadsheet_id()
        
        # Get the latest clipboard content from the cloud
        content, system_id, timestamp = get_latest_cloud_clipboard()
        
        if not content:
            print("No clipboard content found in cloud.")
            return False
        
        # Get the current system's ID
        current_system_id = socket.gethostname()
        
        # Only update local clipboard if content is from a different system
        if system_id == current_system_id:
            print(f"Latest clipboard content is already from this system ({current_system_id}). No update needed.")
            return False
        
        # Update the local system clipboard
        pyperclip.copy(content)
        print(f"Local clipboard updated with content from system {system_id}")
        print(f"Content length: {len(content)} characters")
        return True
        
    except Exception as e:
        print(f"Error syncing clipboard from cloud: {e}")
        return False

def set_clipboard_content(content):
    """
    Set system clipboard content.
    
    Args:
        content (str): Content to set in clipboard
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import pyperclip
        pyperclip.copy(content)
        return True
    except Exception as e:
        print(f"Error setting clipboard content: {e}")
        return False

def main():
    """
    Main function to capture clipboard and system info and update Google Sheet.
    """
    try:
        # Initialize sheets service
        initialization.initialize_sheets_service()
        initialization.load_spreadsheet_id()
        initialization.check_and_reset_sheet()
        
        # Parse command line arguments
        import argparse
        
        parser = argparse.ArgumentParser(description='Clipboard Cloud Sync')
        parser.add_argument('--pull', action='store_true', help='Pull clipboard from cloud to local system')
        parser.add_argument('--push', action='store_true', help='Push local clipboard to cloud')
        
        args = parser.parse_args()
        
        if args.pull:
            # Get clipboard from cloud and update local clipboard
            sync_from_cloud_to_local()
        
        elif args.push:
            # Get local clipboard content
            content = get_clipboard_content()
            # Get system info
            system_info = get_system_info()
            # Get current datetime
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Add entry to Google Sheet
            initialization.add_clipboard_entry(content, now, system_info)
        
        else:
            print("Please specify --pull or --push")
    
    except Exception as e:
        print(f"Error in main function: {e}")
        # Debug information
        print("\n=== DEBUG INFO ===")
        try:
            print(f"Python version: {platform.python_version()}")
            print(f"System: {platform.system()} {platform.version()}")
            print(f"Machine: {platform.machine()}")
            print(f"Hostname: {socket.gethostname()}")
        except Exception as debug_err:
            print(f"Cannot get system info for debugging: {debug_err}")
            
        # Try to check clipboard access
        try:
            clipboard_test = pyperclip.paste()
            print(f"Debug - Clipboard accessible: {bool(clipboard_test is not None)}")
            print(f"Debug - Clipboard content length: {len(clipboard_test) if clipboard_test else 0}")
        except Exception as clip_err:
            print(f"Debug - Cannot access clipboard: {clip_err}")
        
        sys.exit(1)

if __name__ == "__main__":
    main()