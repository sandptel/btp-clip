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
    
