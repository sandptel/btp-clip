<!DOCTYPE html>
<html>

<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Welcome file</title>
  <link rel="stylesheet" href="https://stackedit.io/style.css" />
</head>

<body class="stackedit">
  <div class="stackedit__left">
    <div class="stackedit__toc">
      
<ul>
<li><a href="#clipboard-sync-system">Clipboard-Sync System</a>
<ul>
<li><a href="#overview">Overview</a></li>
<li><a href="#repository-structure">Repository Structure</a></li>
<li><a href="#features">Features</a></li>
<li><a href="#requirements">Requirements</a></li>
<li><a href="#installation">Installation</a></li>
<li><a href="#linux-x86_64">Linux (x86_64):</a></li>
<li><a href="#macos-arm64">macOS (ARM64):</a></li>
</ul>
</li>
<li><a href="#make-the-binary-executable-1">Make the binary executable</a></li>
<li><a href="#run-the-binary-first-run-will-set-up-oauth-1">Run the binary (first run will set up OAuth)</a>
<ul>
<li><a href="#windows">Windows</a></li>
<li><a href="#first-time-setup">First-Time Setup</a></li>
<li><a href="#usage">Usage</a></li>
<li><a href="#binary-distributions">Binary Distributions</a></li>
<li><a href="#building-from-source">Building from Source</a></li>
<li><a href="#how-it-works">How It Works</a></li>
<li><a href="#troubleshooting">Troubleshooting</a></li>
<li><a href="#advanced-configuration">Advanced Configuration</a></li>
<li><a href="#security-considerations">Security Considerations</a></li>
<li><a href="#limitations">Limitations</a></li>
<li><a href="#support-and-contributions">Support and Contributions</a></li>
</ul>
</li>
</ul>

    </div>
  </div>
  <div class="stackedit__right">
    <div class="stackedit__html">
      <h1 id="clipboard-sync-system">Clipboard-Sync System</h1>
<h2 id="overview">Overview</h2>
<p>Clipboard-Sync is a versatile utility that enables clipboard synchronization and remote command execution across multiple systems using Google Sheets as the synchronization backend. It provides a secure and easy way to share clipboard content and execute commands across different machines, regardless of their operating system or network configuration.</p>
<h2 id="repository-structure">Repository Structure</h2>
<pre><code>clipboard-sync/
├── code.zip                   # Source code archive
├── linux-x86_64-binary/       # Linux binary distribution (64-bit)
├── macos-arm64-binary/        # macOS binary distribution (ARM64)
├── windows-x86_64-binary/     # Windows binary distribution (64-bit)
└── README.md                  # This file
</code></pre>
<h2 id="features">Features</h2>
<ul>
<li><strong>Clipboard Synchronization</strong>: Share clipboard content across multiple devices</li>
<li><strong>Remote Command Execution</strong>: Send commands to be executed on remote systems</li>
<li><strong>Cross-Platform Support</strong>: Works on Windows, macOS, and Linux</li>
<li><strong>No Open Ports Required</strong>: Uses Google Sheets as an intermediary, so no need for port forwarding</li>
<li><strong>Secure Authentication</strong>: OAuth 2.0 authentication with Google</li>
<li><strong>Easy to Use CLI</strong>: Simple command-line interface for all operations</li>
</ul>
<h2 id="requirements">Requirements</h2>
<ul>
<li>Google Account</li>
<li>Internet connection</li>
<li>Python 3.6+ (for source code only)</li>
<li>Google Sheets API enabled in Google Cloud Console (instructions below)</li>
</ul>
<h2 id="installation">Installation</h2>
<h3 id="binary-installation-recommended">Binary Installation (Recommended)</h3>
<p>Choose the appropriate binary distribution for your operating system:</p>
<h2 id="linux-x86_64">Linux (x86_64):</h2>
<h3 id="extract-the-binary">Extract the binary</h3>
<pre><code>unzip  linux-x86_64-binary.zip
cd  linux-x86_64-binary
</code></pre>
<h3 id="make-the-binary-executable">Make the binary executable</h3>
<pre><code>chmod  +x  clipboard-sync
</code></pre>
<h3 id="run-the-binary-first-run-will-set-up-oauth">Run the binary (first run will set up OAuth)</h3>
<pre><code>./clipboard-sync  info
</code></pre>
<h2 id="macos-arm64">macOS (ARM64):</h2>
<h3 id="extract-the-binary-1">Extract the binary</h3>
<pre><code>unzip  macos-arm64-binary.zip
cd  macos-arm64-binary
</code></pre>
<h1 id="make-the-binary-executable-1">Make the binary executable</h1>
<pre><code>chmod  +x  clipboard-sync
</code></pre>
<h1 id="run-the-binary-first-run-will-set-up-oauth-1">Run the binary (first run will set up OAuth)</h1>
<pre><code>./clipboard-sync  info
</code></pre>
<h2 id="windows">Windows</h2>
<h3 id="extract-the-binary-zip-file-using-windows-explorer">Extract the binary ZIP file using Windows Explorer</h3>
<h3 id="open-command-prompt-or-powershell-in-the-extracted-directory">Open Command Prompt or PowerShell in the extracted directory</h3>
<pre><code>cd windows-x86_64-binary
</code></pre>
<h3 id="run-the-binary-first-run-will-set-up-oauth-2">Run the binary (first run will set up OAuth)</h3>
<pre><code>clipboard-sync.exe info
</code></pre>
<h3 id="source-code-installation">Source Code Installation</h3>
<p>If you prefer to install from source:</p>
<pre><code># Extract the source code
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

</code></pre>
<h2 id="first-time-setup">First-Time Setup</h2>
<ol>
<li>Run  <code>clipboard-sync info</code>  to initialize the configuration</li>
<li>On first run, a browser will open for Google OAuth authorization</li>
<li>Log in with your Google account and grant the requested permissions</li>
<li>A new Google Sheet will be created automatically for synchronization</li>
<li>The Sheet ID is stored in  sheets.json  in the application directory</li>
</ol>
<h3 id="setting-up-google-api-only-needed-for-source-code-installation">Setting up Google API (only needed for source code installation)</h3>
<ol>
<li>Go to  Google Cloud Console</li>
<li>Create a new project</li>
<li>Enable the Google Sheets API</li>
<li>Create OAuth 2.0 credentials (Desktop Application type)</li>
<li>Download the credentials JSON file</li>
<li>Rename it to  credentials.json  and place it in the same directory as the application</li>
</ol>
<h2 id="usage">Usage</h2>
<h3 id="basic-commands">Basic Commands</h3>
<pre class=" language-bash"><code class="prism  language-bash">clipboard-sync --help              <span class="token comment"># Show help and available commands</span>
clipboard-sync daemon              <span class="token comment"># Start the daemon for continuous synchronization</span>
clipboard-sync send --command <span class="token string">"ls"</span> --target <span class="token string">"laptop"</span>  <span class="token comment"># Send command to remote system</span>
clipboard-sync check               <span class="token comment"># Check and execute pending commands</span>
clipboard-sync list                <span class="token comment"># List pending commands</span>
clipboard-sync info                <span class="token comment"># Show system info and connection details</span>
</code></pre>
<h3 id="clipboard-synchronization">Clipboard Synchronization</h3>
<p>The clipboard sync daemon continuously monitors your clipboard and synchronizes it across all connected systems:</p>
<pre class=" language-bash"><code class="prism  language-bash"><span class="token comment"># Start the daemon with default settings</span>
clipboard-sync  daemon
<span class="token comment"># Start with custom intervals (in seconds)</span>
clipboard-sync  daemon  --clipboard-interval  10  --command-interval  20
</code></pre>
<h3 id="remote-command-execution">Remote Command Execution</h3>
<p>Send commands to be executed on remote systems:</p>
<pre class=" language-bash"><code class="prism  language-bash"><span class="token comment"># Send a command to another system</span>
clipboard-sync send --command <span class="token string">"ls -la"</span> --target <span class="token string">"laptop-hostname"</span>

<span class="token comment"># Execute a more complex command</span>
clipboard-sync send --command <span class="token string">"find /home -name '*.txt' | xargs grep 'important'"</span> --target <span class="token string">"server"</span>

<span class="token comment"># Run a script</span>
clipboard-sync send --command <span class="token string">"bash /path/to/script.sh"</span> --target <span class="token string">"raspberry-pi"</span>
</code></pre>
<h3 id="checking-for-commands">Checking for Commands</h3>
<p>On the target system, check for and execute pending commands:</p>
<pre><code># Check for pending commands
clipboard-sync check

# List all pending commands without executing them
clipboard-sync list
</code></pre>
<h2 id="binary-distributions">Binary Distributions</h2>
<h3 id="linux-x86_64-binary">Linux x86_64 Binary</h3>
<ul>
<li>Compatible with most 64-bit Linux distributions (Ubuntu, Debian, CentOS, etc.)</li>
<li>Compiled with PyInstaller to include all dependencies</li>
<li>Does not require Python to be installed on the system</li>
</ul>
<h3 id="macos-arm64-binary">macOS ARM64 Binary</h3>
<ul>
<li>Compatible with Apple Silicon Macs (M1, M2, etc.)</li>
<li>Optimized for ARM64 architecture</li>
<li>Includes all dependencies with no external requirements</li>
</ul>
<h3 id="windows-x86_64-binary">Windows x86_64 Binary</h3>
<ul>
<li>Compatible with 64-bit Windows systems (Windows 10, 11)</li>
<li>Includes all required DLLs and dependencies</li>
<li>No installation required, works as a standalone executable</li>
</ul>
<h2 id="building-from-source">Building from Source</h2>
<p>To compile your own binaries from source:</p>
<h3 id="prerequisites">Prerequisites</h3>
<ul>
<li>Python 3.6 or higher</li>
<li>pip package manager</li>
<li>PyInstaller (<code>pip install pyinstaller</code>)</li>
<li>Required Python packages (<code>pip install -r requirements.txt</code>)</li>
</ul>
<h3 id="building-steps">Building Steps</h3>
<h4 id="for-linux">For Linux:</h4>
<pre><code>cd clipboard-sync-source
pyinstaller --onefile --name clipboard-sync application.py
# Binary will be in dist/clipboard-sync
</code></pre>
<h4 id="for-macos">For macOS:</h4>
<pre><code>cd  clipboard-sync-source

pyinstaller  --onefile  --name  clipboard-sync  application.py

# Binary will be in dist/clipboard-sync
</code></pre>
<h4 id="for-windows">For Windows:</h4>
<pre><code>cd clipboard-sync-source
pyinstaller --onefile --name clipboard-sync application.py
# Binary will be in dist\clipboard-sync.exe
</code></pre>
<h2 id="how-it-works">How It Works</h2>
<p>Clipboard-Sync uses Google Sheets as a secure backend for synchronization:</p>
<ol>
<li><strong>Authentication</strong>: OAuth 2.0 is used to securely access your Google account</li>
<li><strong>Storage</strong>: A dedicated Google Sheet is created for clipboard and command data</li>
<li><strong>Synchronization</strong>:
<ul>
<li>Clipboard data is stored in columns A-C</li>
<li>Commands are stored in columns E-H</li>
</ul>
</li>
<li><strong>Command Execution</strong>:
<ul>
<li>Command sender writes to the sheet with target system info</li>
<li>Target system checks the sheet periodically</li>
<li>When a command is found for the target system, it’s executed</li>
<li>Execution logs are written back to the sheet</li>
</ul>
</li>
</ol>
<h2 id="troubleshooting">Troubleshooting</h2>
<h3 id="authentication-issues">Authentication Issues</h3>
<ul>
<li>Ensure  credentials.json  is present (for source installation)</li>
<li>Check that the Google Sheets API is enabled</li>
<li>Delete  token.json  to force re-authentication</li>
</ul>
<h3 id="command-execution-issues">Command Execution Issues</h3>
<ul>
<li>Verify target system name is correct (case-sensitive)</li>
<li>Ensure the daemon is running on the target system</li>
<li>Check for errors in the logs (<code>application.log</code>)</li>
</ul>
<h3 id="connection-problems">Connection Problems</h3>
<ul>
<li>Verify internet connectivity</li>
<li>Check firewall settings to ensure outbound HTTPS is allowed</li>
<li>Confirm Google Sheets is accessible from your location</li>
</ul>
<h2 id="advanced-configuration">Advanced Configuration</h2>
<h3 id="custom-sync-intervals">Custom Sync Intervals</h3>
<pre class=" language-bash"><code class="prism  language-bash"><span class="token comment"># Set clipboard check interval to 3 seconds and command check to 5 seconds</span>
clipboard-sync daemon --clipboard-interval 3 --command-interval 5
</code></pre>
<h3 id="debug-mode">Debug Mode</h3>
<pre><code># Enable verbose logging for troubleshooting
clipboard-sync daemon --debug
</code></pre>
<h3 id="running-as-a-service">Running as a Service</h3>
<h4 id="linux-systemd">Linux (systemd):</h4>
<p>Create  <code>/etc/systemd/system/clipboard-sync.service</code>:</p>
<pre><code>[Unit]
Description=Clipboard Sync Service
After=network.target

[Service]
ExecStart=/path/to/clipboard-sync daemon
Restart=always
User=your-username

[Install]
WantedBy=multi-user.target
</code></pre>
<p>Then enable and start the service:</p>
<pre><code>sudo  systemctl  enable  clipboard-sync.service
sudo  systemctl  start  clipboard-sync.service
</code></pre>
<h4 id="macos-launchd">macOS (launchd):</h4>
<p>Create  <code>~/Library/LaunchAgents/com.user.clipboard-sync.plist</code>:</p>
<pre class=" language-html"><code class="prism  language-html"><span class="token prolog">&lt;?xml version="1.0" encoding="UTF-8"?&gt;</span>
<span class="token doctype">&lt;!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"&gt;</span>
<span class="token tag"><span class="token tag"><span class="token punctuation">&lt;</span>plist</span> <span class="token attr-name">version</span><span class="token attr-value"><span class="token punctuation">=</span><span class="token punctuation">"</span>1.0<span class="token punctuation">"</span></span><span class="token punctuation">&gt;</span></span>
<span class="token tag"><span class="token tag"><span class="token punctuation">&lt;</span>dict</span><span class="token punctuation">&gt;</span></span>
    <span class="token tag"><span class="token tag"><span class="token punctuation">&lt;</span>key</span><span class="token punctuation">&gt;</span></span>Label<span class="token tag"><span class="token tag"><span class="token punctuation">&lt;/</span>key</span><span class="token punctuation">&gt;</span></span>
    <span class="token tag"><span class="token tag"><span class="token punctuation">&lt;</span>string</span><span class="token punctuation">&gt;</span></span>com.user.clipboard-sync<span class="token tag"><span class="token tag"><span class="token punctuation">&lt;/</span>string</span><span class="token punctuation">&gt;</span></span>
    <span class="token tag"><span class="token tag"><span class="token punctuation">&lt;</span>key</span><span class="token punctuation">&gt;</span></span>ProgramArguments<span class="token tag"><span class="token tag"><span class="token punctuation">&lt;/</span>key</span><span class="token punctuation">&gt;</span></span>
    <span class="token tag"><span class="token tag"><span class="token punctuation">&lt;</span>array</span><span class="token punctuation">&gt;</span></span>
        <span class="token tag"><span class="token tag"><span class="token punctuation">&lt;</span>string</span><span class="token punctuation">&gt;</span></span>/path/to/clipboard-sync<span class="token tag"><span class="token tag"><span class="token punctuation">&lt;/</span>string</span><span class="token punctuation">&gt;</span></span>
        <span class="token tag"><span class="token tag"><span class="token punctuation">&lt;</span>string</span><span class="token punctuation">&gt;</span></span>daemon<span class="token tag"><span class="token tag"><span class="token punctuation">&lt;/</span>string</span><span class="token punctuation">&gt;</span></span>
    <span class="token tag"><span class="token tag"><span class="token punctuation">&lt;/</span>array</span><span class="token punctuation">&gt;</span></span>
    <span class="token tag"><span class="token tag"><span class="token punctuation">&lt;</span>key</span><span class="token punctuation">&gt;</span></span>RunAtLoad<span class="token tag"><span class="token tag"><span class="token punctuation">&lt;/</span>key</span><span class="token punctuation">&gt;</span></span>
    <span class="token tag"><span class="token tag"><span class="token punctuation">&lt;</span>true</span><span class="token punctuation">/&gt;</span></span>
    <span class="token tag"><span class="token tag"><span class="token punctuation">&lt;</span>key</span><span class="token punctuation">&gt;</span></span>KeepAlive<span class="token tag"><span class="token tag"><span class="token punctuation">&lt;/</span>key</span><span class="token punctuation">&gt;</span></span>
    <span class="token tag"><span class="token tag"><span class="token punctuation">&lt;</span>true</span><span class="token punctuation">/&gt;</span></span>
<span class="token tag"><span class="token tag"><span class="token punctuation">&lt;/</span>dict</span><span class="token punctuation">&gt;</span></span>
<span class="token tag"><span class="token tag"><span class="token punctuation">&lt;/</span>plist</span><span class="token punctuation">&gt;</span></span>
</code></pre>
<p>Load the service:</p>
<pre><code>launchctl load ~/Library/LaunchAgents/com.user.clipboard-sync.plist
</code></pre>
<h4 id="windows-task-scheduler">Windows (Task Scheduler):</h4>
<ol>
<li>Open Task Scheduler</li>
<li>Create a new task</li>
<li>Set to run at login</li>
<li>Add action: Start program</li>
<li>Program path:  <code>C:\path\to\clipboard-sync.exe</code></li>
<li>Arguments:  <code>daemon</code></li>
</ol>
<h2 id="security-considerations">Security Considerations</h2>
<ul>
<li>All data is stored in your personal Google account</li>
<li>OAuth tokens provide secure access without storing passwords</li>
<li>Commands are only executed if the target system name matches</li>
<li>No open inbound ports required</li>
</ul>
<h2 id="limitations">Limitations</h2>
<ul>
<li>Requires internet connection to sync</li>
<li>Clipboard content is stored in plain text</li>
<li>Large clipboard contents may sync more slowly</li>
<li>Google API quotas apply (unlikely to be reached in normal use)</li>
</ul>
<h2 id="support-and-contributions">Support and Contributions</h2>
<ul>
<li>Report issues on the GitHub repository</li>
<li>Pull requests are welcome</li>
<li>For support, contact the developers via GitHub</li>
</ul>
<blockquote>
<p>Clipboard-Sync was created by Sandeep Patel &amp; Siddharth Gautam</p>
</blockquote>

    </div>
  </div>
</body>

</html>
