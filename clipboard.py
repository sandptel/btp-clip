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

def main():
    """
    Main function to capture clipboard and system info and update Google Sheet.
    """
    try:
        print("Initializing Google Sheets...")
        # Initialize sheets service
        initialize_sheets_service()
        
        # Load spreadsheet ID
        load_spreadsheet_id()
        
        # Check and reset sheet if needed
        check_and_reset_sheet()
        
        # Get current clipboard content
        clipboard_content = get_clipboard_content()
        if not clipboard_content:
            print("Clipboard is empty. Nothing to save.")
            return
        
        # Get current timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get system information
        system_info = get_system_info()
        
        # Add entry to spreadsheet
        print("Saving clipboard content to Google Sheets...")
        print(f"System info: {system_info}")
        print(f"Clipboard length: {len(clipboard_content)} characters")
        print(f"Timestamp: {current_time}")
        
        try:
            add_clipboard_entry(clipboard_content, current_time, system_info)
            print("Clipboard content saved successfully!")
        except Exception as e:
            print(f"Failed to add clipboard entry to Google Sheets: {e}")
            sys.exit(1)
        
    except Exception as e:
        error_message = f"Error in main execution: {e}"
        print(error_message)
        
        # Try to get system information for debugging even if the main flow failed
        try:
            debug_sys_info = socket.gethostname()
            print(f"Debug - System hostname: {debug_sys_info}")
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