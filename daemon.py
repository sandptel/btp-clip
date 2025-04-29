#!/usr/bin/env python3

import os
import sys
import time
import signal
import logging
import traceback
import warnings
from datetime import datetime

# Suppress googleapiclient warnings about discovery_cache
warnings.filterwarnings('ignore', message='file_cache is only supported with oauth2client<4.0.0')

# Import clipboard functions
from clipboard import push_clipboard, pull_clipboard, get_clipboard_content, get_system_info

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'clipboard_daemon.log'))
    ]
)
logger = logging.getLogger('ClipboardDaemon')

# Filter out googleapiclient discovery_cache warnings
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

class ClipboardDaemon:
    def __init__(self, config_path=None):
        """Initialize the clipboard daemon with configuration."""
        self.running = False
        self.system_id = get_system_info()
        self.last_local_content = None
        self.last_cloud_content = None
        self.last_cloud_system = None
        self.last_check_time = 0
        
        # Load config
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'settings.json')
        
        try:
            import json
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = {
                "daemon": {
                    "enabled": True,
                    "sync_clipboard": True,
                    "sync_direction": "both",
                    "local_poll_interval": 2.0,
                    "cloud_poll_interval": 5.0,
                    "min_change_interval": 1.0,
                    "log_level": "INFO"
                }
            }
        
        # Set log level from config
        log_level = self.config.get("daemon", {}).get("log_level", "INFO")
        numeric_level = getattr(logging, log_level.upper(), None)
        if isinstance(numeric_level, int):
            logger.setLevel(numeric_level)
    
    def start(self):
        """Start the daemon."""
        if self.running:
            logger.warning("Daemon is already running")
            return
        
        self.running = True
        logger.info(f"Starting clipboard daemon on system {self.system_id}")
        
        # Initialize last clipboard content
        self.last_local_content = get_clipboard_content()
        logger.info(f"Initial local clipboard content length: {len(self.last_local_content)}")
        
        # Start monitoring threads
        if self.config.get("daemon", {}).get("sync_clipboard", True):
            self._start_clipboard_monitoring()
    
    def stop(self):
        """Stop the daemon."""
        logger.info("Stopping daemon")
        self.running = False
    
    def _start_clipboard_monitoring(self):
        """Start the clipboard monitoring thread."""
        import threading
        
        threading.Thread(
            target=self._monitor_clipboard,
            daemon=True
        ).start()
    
    def _monitor_clipboard(self):
        """
        Monitor both local and cloud clipboards for changes.
        Only sync when actual changes are detected.
        """
        logger.info("Starting clipboard monitoring")
        local_interval = float(self.config.get("daemon", {}).get("local_poll_interval", 2.0))
        cloud_interval = float(self.config.get("daemon", {}).get("cloud_poll_interval", 5.0))
        min_change_interval = float(self.config.get("daemon", {}).get("min_change_interval", 1.0))
        
        local_timer = 0
        cloud_timer = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Check local clipboard for changes
                if current_time - local_timer >= local_interval:
                    local_timer = current_time
                    current_content = get_clipboard_content()
                    
                    # Only push if content has changed and enough time has passed since last change
                    if (current_content != self.last_local_content and 
                        current_time - self.last_check_time >= min_change_interval):
                        
                        logger.info(f"Local clipboard changed (length: {len(current_content)})")
                        
                        # Only push if sync direction allows
                        if self.config.get("daemon", {}).get("sync_direction") in ["both", "local_to_cloud"]:
                            logger.debug("Pushing to cloud")
                            push_clipboard()
                            self.last_check_time = current_time
                        
                        # Update our record of local clipboard
                        self.last_local_content = current_content
                
                # Check cloud clipboard for changes
                if current_time - cloud_timer >= cloud_interval:
                    cloud_timer = current_time
                    
                    # Only pull if sync direction allows
                    if self.config.get("daemon", {}).get("sync_direction") in ["both", "cloud_to_local"]:
                        logger.debug("Checking cloud for changes")
                        
                        # The pull_clipboard function only updates local if:
                        # 1. Cloud content changed
                        # 2. Change is from a different system
                        pull_result = pull_clipboard()
                        
                        if pull_result:
                            # If pull was successful, update our local content record
                            self.last_local_content = get_clipboard_content()
                            self.last_check_time = current_time
                
                # Sleep briefly to prevent high CPU usage
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in clipboard monitor: {e}")
                logger.debug(traceback.format_exc())
                time.sleep(min(local_interval, cloud_interval))
    
    def restart_sync(self):
        """Reset tracking variables to force a fresh sync."""
        logger.info("Resetting clipboard sync tracking")
        self.last_local_content = None
        self.last_cloud_content = None
        self.last_cloud_system = None
        self.last_check_time = 0

# Global daemon instance
daemon = None

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