# Clipboard-Sync System

## Overview

Clipboard-Sync is a versatile utility that enables clipboard synchronization and remote command execution across multiple systems using Google Sheets as the synchronization backend. It provides a secure and easy way to share clipboard content and execute commands across different machines, regardless of their operating system or network configuration.

## Repository Structure
```
clipboard-sync/
├── code.zip                   # Source code archive
├── linux-x86_64-binary/       # Linux binary distribution (64-bit)
├── macos-arm64-binary/        # macOS binary distribution (ARM64)
├── windows-x86_64-binary/     # Windows binary distribution (64-bit)
└── README.md                  # This file
```

## Features

-   **Clipboard Synchronization**: Share clipboard content across multiple devices
-   **Remote Command Execution**: Send commands to be executed on remote systems
-   **Cross-Platform Support**: Works on Windows, macOS, and Linux
-   **No Open Ports Required**: Uses Google Sheets as an intermediary, so no need for port forwarding
-   **Secure Authentication**: OAuth 2.0 authentication with Google
-   **Easy to Use CLI**: Simple command-line interface for all operations

## Requirements

-   Google Account
-   Internet connection
-   Python 3.6+ (for source code only)
-   Google Sheets API enabled in Google Cloud Console (instructions below)

## Installation

### Binary Installation (Recommended)

Choose the appropriate binary distribution for your operating system:

## Linux (x86_64):

### Extract the binary

    unzip  linux-x86_64-binary.zip
    cd  linux-x86_64-binary

### Make the binary executable

    chmod  +x  clipboard-sync

### Run the binary (first run will set up OAuth)

    ./clipboard-sync  info
    
## macOS (ARM64):
### Extract the binary
    unzip  macos-arm64-binary.zip
    cd  macos-arm64-binary

# Make the binary executable

    chmod  +x  clipboard-sync

# Run the binary (first run will set up OAuth)

    ./clipboard-sync  info
## Windows
### Extract the binary ZIP file using Windows Explorer

### Open Command Prompt or PowerShell in the extracted directory

    cd windows-x86_64-binary

### Run the binary (first run will set up OAuth)

    clipboard-sync.exe info

### Source Code Installation

If you prefer to install from source:

```
# Extract the source code
unzip code.zip
cd clipboard-sync-source

# Install dependencies
pip install -r requirements.txt

# Make the application executable
chmod +x application.py

# Create a symbolic link (Linux/macOS)
sudo ln -s $(pwd)/application.py /usr/local/bin/clipboard-sync

# Run the application
clipboard-sync info

```

## First-Time Setup

1.  Run  `clipboard-sync info`  to initialize the configuration
2.  On first run, a browser will open for Google OAuth authorization
3.  Log in with your Google account and grant the requested permissions
4.  A new Google Sheet will be created automatically for synchronization
5.  The Sheet ID is stored in  sheets.json  in the application directory

### Setting up Google API (only needed for source code installation)

1.  Go to  Google Cloud Console
2.  Create a new project
3.  Enable the Google Sheets API
4.  Create OAuth 2.0 credentials (Desktop Application type)
5.  Download the credentials JSON file
6.  Rename it to  credentials.json  and place it in the same directory as the application

## Usage
### Basic Commands
```bash
clipboard-sync --help              # Show help and available commands
clipboard-sync daemon              # Start the daemon for continuous synchronization
clipboard-sync send --command "ls" --target "laptop"  # Send command to remote system
clipboard-sync check               # Check and execute pending commands
clipboard-sync list                # List pending commands
clipboard-sync info                # Show system info and connection details
```
### Clipboard Synchronization
The clipboard sync daemon continuously monitors your clipboard and synchronizes it across all connected systems:
```bash
# Start the daemon with default settings
clipboard-sync  daemon
# Start with custom intervals (in seconds)
clipboard-sync  daemon  --clipboard-interval  10  --command-interval  20
```

### Remote Command Execution
Send commands to be executed on remote systems:
```bash
# Send a command to another system
clipboard-sync send --command "ls -la" --target "laptop-hostname"

# Execute a more complex command
clipboard-sync send --command "find /home -name '*.txt' | xargs grep 'important'" --target "server"

# Run a script
clipboard-sync send --command "bash /path/to/script.sh" --target "raspberry-pi"
```

### Checking for Commands

On the target system, check for and execute pending commands:

```
# Check for pending commands
clipboard-sync check

# List all pending commands without executing them
clipboard-sync list
```

## Binary Distributions

### Linux x86_64 Binary

-   Compatible with most 64-bit Linux distributions (Ubuntu, Debian, CentOS, etc.)
-   Compiled with PyInstaller to include all dependencies
-   Does not require Python to be installed on the system

### macOS ARM64 Binary

-   Compatible with Apple Silicon Macs (M1, M2, etc.)
-   Optimized for ARM64 architecture
-   Includes all dependencies with no external requirements

### Windows x86_64 Binary

-   Compatible with 64-bit Windows systems (Windows 10, 11)
-   Includes all required DLLs and dependencies
-   No installation required, works as a standalone executable

## Building from Source

To compile your own binaries from source:

### Prerequisites

-   Python 3.6 or higher
-   pip package manager
-   PyInstaller (`pip install pyinstaller`)
-   Required Python packages (`pip install -r requirements.txt`)

### Building Steps

#### For Linux:

    cd clipboard-sync-source
    pyinstaller --onefile --name clipboard-sync application.py
    # Binary will be in dist/clipboard-sync
#### For macOS:
    cd  clipboard-sync-source
    
    pyinstaller  --onefile  --name  clipboard-sync  application.py
    
    # Binary will be in dist/clipboard-sync

#### For Windows:

    cd clipboard-sync-source
    pyinstaller --onefile --name clipboard-sync application.py
    # Binary will be in dist\clipboard-sync.exe

## How It Works

Clipboard-Sync uses Google Sheets as a secure backend for synchronization:

1.  **Authentication**: OAuth 2.0 is used to securely access your Google account
2.  **Storage**: A dedicated Google Sheet is created for clipboard and command data
3.  **Synchronization**:
    -   Clipboard data is stored in columns A-C
    -   Commands are stored in columns E-H
4.  **Command Execution**:
    -   Command sender writes to the sheet with target system info
    -   Target system checks the sheet periodically
    -   When a command is found for the target system, it's executed
    -   Execution logs are written back to the sheet

## Troubleshooting

### Authentication Issues

-   Ensure  credentials.json  is present (for source installation)
-   Check that the Google Sheets API is enabled
-   Delete  token.json  to force re-authentication

### Command Execution Issues

-   Verify target system name is correct (case-sensitive)
-   Ensure the daemon is running on the target system
-   Check for errors in the logs (`application.log`)

### Connection Problems

-   Verify internet connectivity
-   Check firewall settings to ensure outbound HTTPS is allowed
-   Confirm Google Sheets is accessible from your location

## Advanced Configuration

### Custom Sync Intervals

```bash
# Set clipboard check interval to 3 seconds and command check to 5 seconds
clipboard-sync daemon --clipboard-interval 3 --command-interval 5
```

### Debug Mode

    # Enable verbose logging for troubleshooting
    clipboard-sync daemon --debug

### Running as a Service

#### Linux (systemd):

Create  `/etc/systemd/system/clipboard-sync.service`:
```
[Unit]
Description=Clipboard Sync Service
After=network.target

[Service]
ExecStart=/path/to/clipboard-sync daemon
Restart=always
User=your-username

[Install]
WantedBy=multi-user.target
```
Then enable and start the service:

    sudo  systemctl  enable  clipboard-sync.service
    sudo  systemctl  start  clipboard-sync.service

#### macOS (launchd):

Create  `~/Library/LaunchAgents/com.user.clipboard-sync.plist`:

```html
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.clipboard-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/clipboard-sync</string>
        <string>daemon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```
Load the service:

    launchctl load ~/Library/LaunchAgents/com.user.clipboard-sync.plist

#### Windows (Task Scheduler):

1.  Open Task Scheduler
2.  Create a new task
3.  Set to run at login
4.  Add action: Start program
5.  Program path:  `C:\path\to\clipboard-sync.exe`
6.  Arguments:  `daemon`

## Security Considerations

-   All data is stored in your personal Google account
-   OAuth tokens provide secure access without storing passwords
-   Commands are only executed if the target system name matches
-   No open inbound ports required

## Limitations

-   Requires internet connection to sync
-   Clipboard content is stored in plain text
-   Large clipboard contents may sync more slowly
-   Google API quotas apply (unlikely to be reached in normal use)

## Support and Contributions

-   Report issues on the GitHub repository
-   Pull requests are welcome
-   For support, contact the developers via GitHub

> Clipboard-Sync was created by Sandeep Patel & Siddharth Gautam
