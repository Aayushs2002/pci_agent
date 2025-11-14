PCI Compliance Agent v1.0.0
================================

INSTALLATION INSTRUCTIONS
-------------------------

1. Extract all files from the ZIP to a folder
2. Right-click install.bat and select "Run as administrator"
3. Follow the on-screen instructions

The agent will be installed to:
  C:\Program Files\PCI-Compliance-Agent\

FILES INCLUDED
--------------

  pci-agent.exe    - The agent executable
  config.yaml      - Configuration file
  install.bat      - Installation script
  launcher.bat     - User-friendly launcher (NEW!)
  README.txt       - This file

CONFIGURATION
-------------

Before starting the agent, edit the configuration file:
  C:\Program Files\PCI-Compliance-Agent\config.yaml

Important settings to configure:
  - server_url: Your PCI compliance server address
  - websocket_url: WebSocket server address (usually same as server)
  - scan directories: Paths to scan for PAN data

STARTING THE AGENT
------------------

Option 1: User-Friendly Launcher (RECOMMENDED)
  cd "C:\Program Files\PCI-Compliance-Agent"
  launcher.bat
  
  This will show a menu with options:
  1. Start Agent (Connect to Server)
  2. Run Quick Scan
  3. Show Agent Information
  4. Exit

Option 2: WebSocket Mode (Command Line)
  cd "C:\Program Files\PCI-Compliance-Agent"
  pci-agent.exe --websocket-mode --server-url http://your-server:3001

Option 3: Direct Scan Mode (Command Line)
  cd "C:\Program Files\PCI-Compliance-Agent"
  pci-agent.exe --operator "Your Name" --directories C:\path\to\scan

WHY BLACK SCREEN?
-----------------

If you double-click pci-agent.exe directly, you'll see a black screen
that quickly disappears. This is NORMAL because:

  - The agent is a command-line tool that requires parameters
  - It needs to know what to do (scan, connect to server, etc.)
  - Without parameters, it shows help and exits

SOLUTION: Use launcher.bat instead!
  - Double-click launcher.bat
  - Choose from the menu what you want to do
  - It will prompt you for server URL or scan directory

TROUBLESHOOTING
---------------

If installation fails:
  - Make sure you extracted ALL files from the ZIP
  - Run install.bat as Administrator
  - Check if antivirus is blocking the files
  - Ensure you have write access to C:\Program Files

If the agent won't start:
  - Check the configuration file syntax
  - Verify server URL is correct and reachable
  - Check logs in C:\Program Files\PCI-Compliance-Agent\logs\
  - Make sure you're using HTTP (not HTTPS) if server is on port 3001

If you see "black screen":
  - Use launcher.bat instead of clicking pci-agent.exe
  - Or run from command prompt with proper arguments

For more information:
  - Documentation: https://github.com/your-repo
  - Support: support@yourcompany.com
