# Cloud Clipboard Sync

A cross-platform clipboard synchronization tool that allows you to share clipboard content across multiple devices using Google Sheets as storage.

## Features

- **Real-time Clipboard Synchronization**: Share clipboard content across devices
- **System-Aware**: Only updates local clipboard when content comes from a different system
- **Supports Multiple Platforms**: Works on Windows, macOS, and Linux
- **Low Resource Usage**: Efficient monitoring with minimal CPU and memory footprint
- **Robust Error Handling**: Recovers automatically from network errors
- **System Integration**: Runs as a proper daemon with support for system signals

## Requirements

- Python 3.6 or higher
- Google account for Google Sheets access
- Internet connection

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/cloud-clipboard-sync.git
cd cloud-clipboard-sync
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up Google Sheets API access**

   a. Go to the [Google Cloud Console](https://console.cloud.google.com/)
   
   b. Create a new project
   
   c. Enable the Google Sheets API for your project
   
   d. Create OAuth 2.0 credentials:
      - Select "Desktop app" as application type
      - Download the credentials JSON file
   
   e. Rename the downloaded file to 

credentials.json

 and place it in the project directory

## Configuration

1. **Create a settings file**

Create a file named 

settings.json

 in the project directory with the following content:

```json
{
  "daemon": {
    "enabled": true,
    "sync_clipboard": true,
    "sync_direction": "both",
    "local_poll_interval": 2.0,
    "cloud_poll_interval": 5.0,
    "min_change_interval": 1.0,
    "log_level": "INFO"
  },
  "spreadsheet_id": ""
}
```

Note: Leave the `spreadsheet_id` empty for now. The program will create a new spreadsheet on first run.

2. **Customize settings (optional)**

- `sync_direction`: Set to "both", "local_to_cloud", or "cloud_to_local"
- `local_poll_interval`: How often to check for local clipboard changes (in seconds)
- `cloud_poll_interval`: How often to check for cloud clipboard changes (in seconds)
- `min_change_interval`: Minimum time between syncs (in seconds)
- `log_level`: Set to "DEBUG", "INFO", "WARNING", or "ERROR"

## Usage

### First Run

Run the program manually to authorize Google Sheets access:

```bash
python clipboard.py --push
```

This will:
1. Open a browser window requesting Google account authorization
2. Create a new Google Sheets spreadsheet (if none exists)
3. Save the spreadsheet ID to your settings file
4. Push your current clipboard to the cloud

### Running the Daemon

Start the clipboard synchronization daemon:

```bash
python daemon.py
```

The daemon will continuously:
- Monitor your local clipboard for changes and push them to Google Sheets
- Check Google Sheets for clipboard content from other systems and update your local clipboard

### Manual Operations

Push local clipboard to cloud:
```bash
python clipboard.py --push
```

Pull cloud clipboard to local (only if from another system):
```bash
python clipboard.py --pull
```

Print debug information:
```bash
python clipboard.py --debug
```

### Running as a System Service

#### Linux (systemd)

1. Create a systemd service file:
```bash
sudo nano /etc/systemd/system/clipboard-sync.service
```

2. Add the following content (update paths):
```
[Unit]
Description=Cloud Clipboard Sync Daemon
After=network.target

[Service]
Type=simple
User=yourusername
ExecStart=/usr/bin/python3 /path/to/daemon.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:
```bash
sudo systemctl enable clipboard-sync.service
sudo systemctl start clipboard-sync.service
```

## Troubleshooting

### Check logs
```bash
tail -f clipboard_daemon.log
```

### Common issues:

1. **Authentication errors**: Delete 

token.json

 and run the program again to re-authenticate

2. **Clipboard access errors**: 
   - On Linux, make sure `xclip` or `xsel` is installed
   - On macOS, clipboard access may require extra permissions
   - On headless systems, clipboard access may not be available

3. **Network errors**: The daemon will automatically retry and recover from temporary network issues

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Pyperclip](https://github.com/asweigart/pyperclip) for cross-platform clipboard access
- [Google Sheets API](https://developers.google.com/sheets/api) for cloud storage
