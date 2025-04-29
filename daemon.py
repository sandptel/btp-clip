#!/usr/bin/env python3

import os
import sys
import time
import json
import signal
import logging
import platform
import threading
import pyperclip
import traceback

# Add imports for notifications
from plyer import notification

# Import functions from initialization.py
from initialization import (
    initialize_sheets_service,
    load_spreadsheet_id,
    check_and_reset_sheet,
    add_clipboard_entry
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'clipboard_daemon.log'))
    ]
)
logger = logging.getLogger('ClipboardDaemon')

class ClipboardDaemon:
    def __init__(self, config_path=None):
        """Initialize the clipboard daemon with configuration."""
        self.running = False
        self.last_local_clipboard = ""
        self.last_cloud_clipboard = ""
        self.last_uploaded_content = ""  # Track what we last uploaded to avoid echo effects
        self.syncing_cloud_to_local = False
        self.system_id = self._generate_system_id()  # Generate a unique ID for this system
        
        # Load config
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'settings.json')
        
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = {
                "daemon": {
                    "enabled": False,
                    "sync_clipboard": True,
                    "sync_direction": "both",
                    "local_poll_interval": 1.0,
                    "cloud_poll_interval": 5.0,
                    "log_level": "INFO"
                }
            }
        
        # Set log level from config
        log_level = self.config.get("daemon", {}).get("log_level", "INFO")
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logger.setLevel(numeric_level)
        
        # Initialize Google Sheets service
        try:
            initialize_sheets_service()
            load_spreadsheet_id()
            check_and_reset_sheet()
            logger.info("Google Sheets service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
            if self.config.get("daemon", {}).get("sync_clipboard", False):
                logger.warning("Clipboard sync is enabled but Google Sheets initialization failed")
            error_msg = f"Failed to initialize Google Sheets service: {str(e)}"
            logger.error(error_msg)
            self._send_notification("Clipboard Sync Error", error_msg)
    
    def _generate_system_id(self):
        """Generate a unique identifier for this system."""
        import socket
        import uuid
        
        # Combine hostname and a machine UUID to create a system identifier
        hostname = socket.gethostname()
        machine_id = str(uuid.getnode())  # MAC address as integer
        system_id = f"{hostname}-{machine_id}"
        logger.info(f"System identifier: {system_id}")
        return system_id

    def start(self):
        """Start the daemon."""
        if self.running:
            logger.warning("Daemon is already running")
            return
        
        # Check if daemon is enabled in config
        if not self.config.get("daemon", {}).get("enabled", False):
            logger.info("Daemon is disabled in configuration. Exiting.")
            return
        
        self.running = True
        logger.info("Starting clipboard daemon")
        
        # Start threads if clipboard sync is enabled
        if self.config.get("daemon", {}).get("sync_clipboard", False):
            sync_direction = self.config.get("daemon", {}).get("sync_direction", "both")
            
            if sync_direction in ["both", "local_to_cloud"]:
                local_interval = self.config.get("daemon", {}).get("local_poll_interval", 1.0)
                self.local_monitor_thread = threading.Thread(
                    target=self._monitor_local_clipboard, 
                    args=(local_interval,)
                )
                self.local_monitor_thread.daemon = True
                self.local_monitor_thread.start()
                logger.info(f"Local clipboard monitoring started (interval: {local_interval}s)")
            
            if sync_direction in ["both", "cloud_to_local"]:
                cloud_interval = self.config.get("daemon", {}).get("cloud_poll_interval", 5.0)
                self.cloud_monitor_thread = threading.Thread(
                    target=self._monitor_cloud_clipboard, 
                    args=(cloud_interval,)
                )
                self.cloud_monitor_thread.daemon = True
                self.cloud_monitor_thread.start()
                logger.info(f"Cloud clipboard monitoring started (interval: {cloud_interval}s)")
        else:
            logger.info("Clipboard sync is disabled in configuration")
    
    def stop(self):
        """Stop the daemon."""
        logger.info("Stopping clipboard daemon")
        self.running = False
    
    def _monitor_local_clipboard(self, interval):
        """Monitor local clipboard for changes and upload to cloud."""
        logger.info("Starting local clipboard monitor thread")
        self.last_local_clipboard = pyperclip.paste() or ""
        
        while self.running:
            try:
                # Skip if we're currently syncing from cloud to local
                if self.syncing_cloud_to_local:
                    time.sleep(interval)
                    continue
                
                current_clipboard = pyperclip.paste() or ""
                
                # Check if clipboard changed
                if current_clipboard != self.last_local_clipboard:
                    logger.info(f"Local clipboard changed (length: {len(current_clipboard)})")
                    
                    # Check if we should ignore empty clipboard content
                    if not current_clipboard and self.config.get("clipboard", {}).get("ignore_empty", True):
                        logger.info("Empty clipboard content, ignoring")
                    # Check if we should ignore unchanged clipboard content
                    elif current_clipboard == self.last_cloud_clipboard:
                        logger.info("Clipboard content is the same as cloud, ignoring")
                    else:
                        # Upload to Google Sheets
                        from datetime import datetime
                        import socket
                        
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        system_info = f"Host: {socket.gethostname()} | OS: {platform.platform()}"
                        
                        # Truncate if too long
                        max_size = self.config.get("clipboard", {}).get("max_size", 50000)
                        if len(current_clipboard) > max_size:
                            logger.warning(f"Clipboard content too long ({len(current_clipboard)} bytes), truncating to {max_size}")
                            current_clipboard = current_clipboard[:max_size] + "... (truncated)"
                        
                        # Upload to Google Sheets
                        try:
                            add_clipboard_entry(current_clipboard, timestamp, system_info)
                            logger.info("Uploaded clipboard content to Google Sheets")
                            
                            # Update last cloud clipboard
                            self.last_cloud_clipboard = current_clipboard
                        except Exception as e:
                            logger.error(f"Failed to upload clipboard to Google Sheets: {e}")
                    
                    # Update last local clipboard
                    self.last_local_clipboard = current_clipboard
                
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in local clipboard monitor: {e}")
                time.sleep(interval)
    
    def _monitor_cloud_clipboard(self, interval):
        """Monitor cloud clipboard for changes and download to local."""
        logger.info("Starting cloud clipboard monitor thread")
        
        while self.running:
            try:
                # Get the latest clipboard entry from Google Sheets
                from initialization import sheets_service, spreadsheet_id
                
                if not sheets_service or not spreadsheet_id:
                    logger.error("Google Sheets service not initialized")
                    time.sleep(interval)
                    continue
                
                # Get the latest entry (row 2)
                range_name = "Sheet1!A2:A2"  # Cell A2 (first data row)
                result = sheets_service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id, range=range_name).execute()
                values = result.get('values', [])
                
                if values and values[0]:
                    cloud_clipboard = values[0][0]
                    
                    # Check if cloud clipboard changed
                    if cloud_clipboard != self.last_cloud_clipboard:
                        logger.info(f"Cloud clipboard changed (length: {len(cloud_clipboard)})")
                        
                        # Check if different from local clipboard
                        if cloud_clipboard != self.last_local_clipboard:
                            logger.info("Updating local clipboard from cloud")
                            
                            # Set flag to prevent local monitor from uploading this change back
                            self.syncing_cloud_to_local = True
                            
                            # Update local clipboard
                            pyperclip.copy(cloud_clipboard)
                            self.last_local_clipboard = cloud_clipboard
                            
                            # Wait a bit to ensure clipboard update is registered
                            time.sleep(0.5)
                            
                            # Reset flag
                            self.syncing_cloud_to_local = False
                        
                        # Update last cloud clipboard
                        self.last_cloud_clipboard = cloud_clipboard
                
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in cloud clipboard monitor: {e}")
                time.sleep(interval)

    def restart_sync(self):
        """Restart clipboard sync operations after errors"""
        logger.info("Restarting clipboard sync operations")
        # Depending on your implementation you might need to:
        # 1. Reset any sync state/connections
        # 2. Clear error flags
        # 3. Re-initialize sync components
        
        # Example implementation (modify based on your actual daemon structure):
        try:
            # Stop current sync operations if any
            self._stop_sync_operations()
            
            # Reset state
            self._init_sync_state()
            
            # Restart sync operations
            self._start_sync_operations()
            
        except Exception as e:
            logger.error(f"Failed to restart sync: {str(e)}")

    def _send_notification(self, title, message):
        """Send a system notification"""
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Clipboard Sync Daemon",
                timeout=10  # seconds
            )
            logger.debug(f"Push notification sent: {title} - {message}")
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")

    def _check_cloud_clipboard(self):
        """Check if cloud clipboard has changed and update local if needed."""
        try:
            # Get the latest cloud clipboard content and metadata
            cloud_content, source_system = self._get_cloud_clipboard_content()
            
            # Only process if cloud content is different from what we know
            # AND it's from a different system (not our own update)
            if cloud_content != self.last_cloud_clipboard and source_system != self.system_id:
                logger.info(f"Cloud clipboard changed by system {source_system} (length: {len(cloud_content)})")
                
                # Update local clipboard with cloud content
                if self.config.get("daemon", {}).get("sync_direction") in ["both", "cloud_to_local"]:
                    logger.info("Updating local clipboard from cloud")
                    self.syncing_cloud_to_local = True
                    self._set_local_clipboard(cloud_content)
                    self.syncing_cloud_to_local = False
                    
                # Update our record of the last cloud clipboard
                self.last_cloud_clipboard = cloud_content
                
            return cloud_content
            
        except Exception as e:
            logger.error(f"Error checking cloud clipboard: {str(e)}")
            return None
            
    def _check_local_clipboard(self):
        """Check if local clipboard has changed and update cloud if needed."""
        try:
            # Get current local clipboard content
            local_content = self._get_local_clipboard_content()
            
            # Only proceed if content changed and we're not currently syncing from cloud
            if local_content != self.last_local_clipboard and not self.syncing_cloud_to_local:
                logger.info(f"Local clipboard changed (length: {len(local_content)})")
                
                # Update cloud clipboard with local content
                if self.config.get("daemon", {}).get("sync_direction") in ["both", "local_to_cloud"]:
                    logger.info("Uploading clipboard content to Google Sheets")
                    self._set_cloud_clipboard(local_content)
                    self.last_uploaded_content = local_content  # Track what we just uploaded
                    
                # Update our record of the last local clipboard
                self.last_local_clipboard = local_content
                
            return local_content
            
        except Exception as e:
            logger.error(f"Error checking local clipboard: {str(e)}")
            return None
            
    def _set_cloud_clipboard(self, content):
        """Set content to the cloud clipboard (Google Sheets) with system identifier."""
        try:
            # Modify your implementation to include the system_id when updating Google Sheet
            # For example, store both the content and the system_id in different columns
            # ...
            
            # Example implementation:
            # update_google_sheet(content=content, system_id=self.system_id)
            
            # After successful upload, update our tracking variables
            self.last_cloud_clipboard = content
            self.last_uploaded_content = content
            
        except Exception as e:
            logger.error(f"Error setting cloud clipboard: {str(e)}")
            
    def _get_cloud_clipboard_content(self):
        """Get clipboard content from Google Sheets with system ID information."""
        try:
            # Modify your implementation to retrieve both content and source system ID
            # ...
            
            # Example implementation:
            # content, source_system = get_google_sheet_data()
            
            # Return both the content and the source system ID
            return content, source_system
            
        except Exception as e:
            logger.error(f"Error getting cloud clipboard content: {str(e)}")
            return "", ""

def signal_handler(sig, frame):
    """Handle termination signals."""
    logger.info("Received termination signal")
    if daemon:
        daemon.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start daemon
    daemon = ClipboardDaemon()
    daemon.start()
    
    # Track consecutive errors
    consecutive_errors = 0
    max_consecutive_errors = 2
    
    try:
        # Keep main thread alive
        while daemon.running:
            try:
                # If we had consecutive errors and reached threshold, restart sync
                if consecutive_errors >= max_consecutive_errors:
                    logger.warning(f"Encountered {consecutive_errors} consecutive sync errors, restarting sync operations")
                    daemon.restart_sync()
                    consecutive_errors = 0
                
                time.sleep(1)
                
            except Exception as e:
                # Log sync error but don't terminate daemon
                consecutive_errors += 1
                logger.error(f"Error during clipboard sync: {str(e)}")
                logger.debug(f"Error details: {traceback.format_exc()}")
                
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        daemon.stop()