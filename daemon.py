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
        self.syncing_cloud_to_local = False
        
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



if __name__ == "__main__":
    # Register signal handlers
    # signal.signal(signal.SIGINT, signal_handler)
    # signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start daemon
    daemon = ClipboardDaemon()
    daemon.start()
    
    try:
        # Keep main thread alive
        while daemon.running:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        daemon.stop()