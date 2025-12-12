#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Build System
Builds PCI Compliance Agent installers for different platforms
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
import json
import zipfile

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Version info
VERSION = "1.0.0"
AGENT_NAME = "pci-compliance-agent"

# Directories
BUILD_DIR = Path("dist")
INSTALLER_DIR = Path("installers")
TEMP_DIR = Path("build_temp")

def clean_build():
    """Clean previous build artifacts"""
    print("🧹 Cleaning previous builds...")
    dirs_to_clean = [BUILD_DIR, INSTALLER_DIR, TEMP_DIR, Path("build"), Path("__pycache__")]
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  ✓ Removed {dir_path}")

def install_dependencies():
    """Install required build dependencies"""
    print("📦 Installing build dependencies...")
    
    dependencies = [
        "pyinstaller>=5.13.0",
        "setuptools>=68.0.0",
    ]
    
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"  ✓ Installed {dep}")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Failed to install {dep}: {e}")

def build_executable():
    """Build standalone executable using PyInstaller"""
    print(f"🔨 Building executable for {platform.system()}...")
    
    try:
        # Run PyInstaller
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "pci-agent.spec",
            "--clean",
            "--noconfirm"
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        if result.returncode == 0:
            print("  ✓ Executable built successfully")
            return True
        else:
            print(f"  ✗ Build failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ✗ Build error: {e}")
        return False

def create_windows_installer():
    """Create Windows installer (.exe with Inno Setup or ZIP)"""
    print("📦 Creating Windows installer...")
    
    INSTALLER_DIR.mkdir(parents=True, exist_ok=True)
    
    exe_path = BUILD_DIR / "pci-agent.exe"
    if not exe_path.exists():
        print("  ✗ Executable not found")
        return False
    
    # Create installation package directory
    install_pkg_dir = TEMP_DIR / "windows_package"
    install_pkg_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    shutil.copy(exe_path, install_pkg_dir / "pci-agent.exe")
    
    # Create config template
    shutil.copy("config.example.yaml", install_pkg_dir / "config.yaml")
    
    # Copy launcher script if it exists
    if Path("launcher.bat").exists():
        shutil.copy("launcher.bat", install_pkg_dir / "launcher.bat")
    
    # Create installation script
    install_script = install_pkg_dir / "install.bat"
    install_script.write_text("""@echo off
echo PCI Compliance Agent Installer
echo ==============================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This installer must be run as Administrator!
    echo Right-click install.bat and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

REM Get the directory where the script is located
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Check if files exist
if not exist "%SCRIPT_DIR%pci-agent.exe" (
    echo ERROR: pci-agent.exe not found in current directory!
    echo Please make sure you extracted all files from the ZIP.
    echo Current directory: %SCRIPT_DIR%
    echo.
    pause
    exit /b 1
)

if not exist "%SCRIPT_DIR%config.yaml" (
    echo ERROR: config.yaml not found in current directory!
    echo Please make sure you extracted all files from the ZIP.
    echo Current directory: %SCRIPT_DIR%
    echo.
    pause
    exit /b 1
)

REM Create installation directory
set INSTALL_DIR=C:\\Program Files\\PCI-Compliance-Agent
echo Creating installation directory: %INSTALL_DIR%
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy files
echo Copying files...
copy /Y "%SCRIPT_DIR%pci-agent.exe" "%INSTALL_DIR%\\pci-agent.exe"
if %errorlevel% neq 0 (
    echo ERROR: Failed to copy pci-agent.exe
    pause
    exit /b 1
)
echo   - pci-agent.exe copied

copy /Y "%SCRIPT_DIR%config.yaml" "%INSTALL_DIR%\\config.yaml"
if %errorlevel% neq 0 (
    echo ERROR: Failed to copy config.yaml
    pause
    exit /b 1
)
echo   - config.yaml copied

REM Copy launcher if exists
if exist "%SCRIPT_DIR%launcher.bat" (
    copy /Y "%SCRIPT_DIR%launcher.bat" "%INSTALL_DIR%\\launcher.bat"
    echo   - launcher.bat copied
)

REM Create logs and reports directories
echo Creating directories...
if not exist "%INSTALL_DIR%\\logs" mkdir "%INSTALL_DIR%\\logs"
echo   - logs directory created
if not exist "%INSTALL_DIR%\\reports" mkdir "%INSTALL_DIR%\\reports"
echo   - reports directory created

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Agent location: %INSTALL_DIR%
echo Configuration: %INSTALL_DIR%\\config.yaml
echo Logs: %INSTALL_DIR%\\logs
echo Reports: %INSTALL_DIR%\\reports
echo.
echo IMPORTANT: Edit the configuration file to set your server URL:
echo   notepad "%INSTALL_DIR%\\config.yaml"
echo.
echo To start the agent:
echo   Option 1: Double-click launcher.bat (User-friendly menu)
echo   Option 2: Use command line:
echo     cd "%INSTALL_DIR%"
echo     pci-agent.exe --websocket-mode --server-url http://your-server:3001
echo.
pause
""")
    
    # Create README
    readme = install_pkg_dir / "README.txt"
    readme.write_text(f"""PCI Compliance Agent v{VERSION}
================================

INSTALLATION INSTRUCTIONS
-------------------------

1. Extract all files from the ZIP to a folder
2. Right-click install.bat and select "Run as administrator"
3. Follow the on-screen instructions

The agent will be installed to:
  C:\\Program Files\\PCI-Compliance-Agent\\

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
  C:\\Program Files\\PCI-Compliance-Agent\\config.yaml

Important settings to configure:
  - server_url: Your PCI compliance server address
  - websocket_url: WebSocket server address (usually same as server)
  - scan directories: Paths to scan for PAN data

STARTING THE AGENT
------------------

Option 1: User-Friendly Launcher (RECOMMENDED)
  cd "C:\\Program Files\\PCI-Compliance-Agent"
  launcher.bat
  
  This will show a menu with options:
  1. Start Agent (Connect to Server)
  2. Run Quick Scan
  3. Show Agent Information
  4. Exit

Option 2: WebSocket Mode (Command Line)
  cd "C:\\Program Files\\PCI-Compliance-Agent"
  pci-agent.exe --websocket-mode --server-url http://your-server:3001

Option 3: Direct Scan Mode (Command Line)
  cd "C:\\Program Files\\PCI-Compliance-Agent"
  pci-agent.exe --operator "Your Name" --directories C:\\path\\to\\scan

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
  - Ensure you have write access to C:\\Program Files

If the agent won't start:
  - Check the configuration file syntax
  - Verify server URL is correct and reachable
  - Check logs in C:\\Program Files\\PCI-Compliance-Agent\\logs\\
  - Make sure you're using HTTP (not HTTPS) if server is on port 3001

If you see "black screen":
  - Use launcher.bat instead of clicking pci-agent.exe
  - Or run from command prompt with proper arguments

For more information:
  - Documentation: https://github.com/your-repo
  - Support: support@yourcompany.com
""")
    
    # Create a helper script to start the agent
    start_script = install_pkg_dir / "start_agent.bat"
    start_script.write_text("""@echo off
echo PCI Compliance Agent Starter
echo ============================
echo.

set INSTALL_DIR=C:\\Program Files\\PCI-Compliance-Agent

if not exist "%INSTALL_DIR%\\pci-agent.exe" (
    echo ERROR: Agent not installed!
    echo Please run install.bat first.
    pause
    exit /b 1
)

cd /d "%INSTALL_DIR%"

echo Starting PCI Compliance Agent...
echo.
echo Press Ctrl+C to stop the agent
echo.

REM Prompt for server URL if not configured
set /p SERVER_URL="Enter server URL (e.g., http://192.168.56.1:3001): "

if "%SERVER_URL%"=="" (
    echo ERROR: Server URL is required
    pause
    exit /b 1
)

REM Start the agent
pci-agent.exe --websocket-mode --server-url %SERVER_URL%

pause
""")
    
    # Create ZIP package
    zip_path = INSTALLER_DIR / f"{AGENT_NAME}-{VERSION}-windows-x64.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in install_pkg_dir.rglob('*'):
            if file.is_file():
                arcname = file.relative_to(install_pkg_dir)
                zipf.write(file, arcname)
    
    print(f"  ✓ Created: {zip_path}")
    print(f"  📦 Size: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    return True

def create_linux_installer():
    """Create Linux installer (.rpm or .deb)"""
    print("📦 Creating Linux installer...")
    
    INSTALLER_DIR.mkdir(parents=True, exist_ok=True)
    
    # PyInstaller creates either dist/pci-agent (single file) or dist/pci-agent/ (directory)
    # When COLLECT is used, the actual binary might be dist/pci-agent/pci-agent
    exe_path = BUILD_DIR / "pci-agent"
    
    if exe_path.is_dir():
        # If it's a directory, look for the executable inside
        potential_exe = exe_path / "pci-agent"
        if potential_exe.exists() and not potential_exe.is_dir():
            exe_path = potential_exe
        else:
            # Look for any executable file in the directory
            for item in exe_path.iterdir():
                if item.is_file() and item.name == "pci-agent":
                    exe_path = item
                    break
    
    if not exe_path.exists() or exe_path.is_dir():
        print(f"  ✗ Executable not found at {exe_path}")
        print(f"  ✗ Is directory: {exe_path.is_dir() if exe_path.exists() else 'N/A'}")
        # Debug: list what's in dist/
        if BUILD_DIR.exists():
            print(f"  Debug: Contents of {BUILD_DIR}:")
            for item in BUILD_DIR.iterdir():
                print(f"    - {item.name} ({'dir' if item.is_dir() else 'file'})")
                if item.is_dir() and item.name == "pci-agent":
                    print(f"      Contents of {item.name}:")
                    for subitem in item.iterdir():
                        print(f"        - {subitem.name} ({'dir' if subitem.is_dir() else 'file'})")
        return False
    
    # Create package structure
    pkg_dir = TEMP_DIR / "linux_package"
    pkg_structure = {
        "usr/local/bin": None,
        "etc/pci-compliance-agent": None,
        "var/log/pci-compliance-agent": None,
        "var/lib/pci-compliance-agent/reports": None,
        "usr/share/doc/pci-compliance-agent": None,
    }
    
    for path_str in pkg_structure.keys():
        path = pkg_dir / path_str
        path.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    shutil.copy(exe_path, pkg_dir / "usr/local/bin/pci-agent")
    os.chmod(pkg_dir / "usr/local/bin/pci-agent", 0o755)
    
    # Copy config
    shutil.copy("config.example.yaml", 
                pkg_dir / "etc/pci-compliance-agent/config.yaml")
    
    # Create systemd service file
    service_file = pkg_dir / "etc/systemd/system"
    service_file.mkdir(parents=True, exist_ok=True)
    
    (service_file / "pci-agent.service").write_text(f"""[Unit]
Description=PCI Compliance Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/etc/pci-compliance-agent
ExecStart=/usr/local/bin/pci-agent --websocket-mode --server-url http://192.168.56.1:3001
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
""")
    
    # Create install script
    install_script = pkg_dir / "install.sh"
    install_script.write_text(f"""#!/bin/bash
# PCI Compliance Agent Installer v{VERSION}

echo "PCI Compliance Agent Installer"
echo "=============================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Copy files
echo "Installing agent..."
cp -f usr/local/bin/pci-agent /usr/local/bin/
chmod +x /usr/local/bin/pci-agent

# Copy configuration
mkdir -p /etc/pci-compliance-agent
cp -f etc/pci-compliance-agent/config.yaml /etc/pci-compliance-agent/

# Create directories
mkdir -p /var/log/pci-compliance-agent
mkdir -p /var/lib/pci-compliance-agent/reports

# Install systemd service (optional)
if [ -d "/etc/systemd/system" ]; then
    cp -f etc/systemd/system/pci-agent.service /etc/systemd/system/
    systemctl daemon-reload
    echo ""
    echo "Systemd service installed. To enable:"
    echo "  systemctl enable pci-agent"
    echo "  systemctl start pci-agent"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Configuration file: /etc/pci-compliance-agent/config.yaml"
echo "Executable: /usr/local/bin/pci-agent"
echo ""
echo "To start the agent:"
echo "  pci-agent --websocket-mode --server-url http://your-server:3001"
echo ""
""")
    os.chmod(install_script, 0o755)
    
    # Create README
    readme = pkg_dir / "README.md"
    readme.write_text(f"""# PCI Compliance Agent v{VERSION}

## Installation

```bash
sudo ./install.sh
```

## Configuration

Edit `/etc/pci-compliance-agent/config.yaml` to configure:
- Server URL
- Scan directories
- Detection settings

## Starting the Agent

### As a Service (Systemd)
```bash
sudo systemctl enable pci-agent
sudo systemctl start pci-agent
```

### Manual Mode
```bash
# WebSocket mode (remote control)
pci-agent --websocket-mode --server-url http://your-server:3001

# CLI mode (direct scan)
pci-agent --operator "Your Name" --directories /path/to/scan
```

## Logs
- Application logs: `/var/log/pci-compliance-agent/`
- Reports: `/var/lib/pci-compliance-agent/reports/`
""")
    
    # Create TAR.GZ package
    tar_path = INSTALLER_DIR / f"{AGENT_NAME}-{VERSION}-linux-x64.tar.gz"
    
    import tarfile
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(pkg_dir, arcname=f"{AGENT_NAME}-{VERSION}")
    
    print(f"  ✓ Created: {tar_path}")
    print(f"  📦 Size: {tar_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    return True

def create_metadata():
    """Create metadata file for installers"""
    metadata = {
        "name": AGENT_NAME,
        "version": VERSION,
        "build_date": subprocess.check_output(
            ["date", "+%Y-%m-%d"] if sys.platform != "win32" else ["powershell", "Get-Date -Format 'yyyy-MM-dd'"],
            text=True
        ).strip(),
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "installers": []
    }
    
    # List created installers
    if INSTALLER_DIR.exists():
        for installer in INSTALLER_DIR.iterdir():
            if installer.is_file():
                metadata["installers"].append({
                    "filename": installer.name,
                    "size": installer.stat().st_size,
                    "platform": "windows" if "windows" in installer.name else "linux"
                })
    
    metadata_file = INSTALLER_DIR / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2))
    print(f"  ✓ Created metadata: {metadata_file}")

def main():
    """Main build process"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build PCI Compliance Agent')
    parser.add_argument('--platform', 
                       choices=['windows', 'linux', 'current', 'all'],
                       default='current',
                       help='Target platform (default: current)')
    parser.add_argument('--skip-build', 
                       action='store_true',
                       help='Skip build step (only create installers from existing build)')
    
    args = parser.parse_args()
    
    print(f"🚀 PCI Compliance Agent Builder v{VERSION}")
    print(f"Host Platform: {platform.system()} {platform.machine()}")
    print(f"Target Platform: {args.platform}")
    print("")
    
    # Determine target platforms
    current_platform = platform.system()
    target_platforms = []
    
    if args.platform == 'current':
        target_platforms = [current_platform]
    elif args.platform == 'all':
        target_platforms = ['Windows', 'Linux']
    elif args.platform == 'windows':
        target_platforms = ['Windows']
    elif args.platform == 'linux':
        target_platforms = ['Linux']
    
    # Clean previous builds
    if not args.skip_build:
        clean_build()
        
        # Install dependencies
        install_dependencies()
        
        # Build executable
        if not build_executable():
            print("❌ Build failed!")
            return False
    
    # Create platform-specific installers
    success = True
    for target in target_platforms:
        print(f"\n📦 Creating {target} installer...")
        
        # Check if we can build for this platform
        if target != current_platform and not args.skip_build:
            print(f"⚠️  Cross-compilation not supported.")
            print(f"   To build for {target}, please run this script on a {target} machine.")
            print(f"   You can manually copy the spec file and source to a {target} system.")
            continue
        
        if target == "Windows":
            if not create_windows_installer():
                print(f"❌ {target} installer creation failed!")
                success = False
        elif target == "Linux":
            if not create_linux_installer():
                print(f"❌ {target} installer creation failed!")
                success = False
        else:
            print(f"⚠️  Platform {target} not fully supported yet")
            print("   Creating basic package...")
            INSTALLER_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create metadata
    create_metadata()
    
    print("")
    if success:
        print("✅ Build completed successfully!")
    else:
        print("⚠️  Build completed with warnings")
    print(f"📂 Installers available in: {INSTALLER_DIR.absolute()}")
    print("")
    
    # List created files
    if INSTALLER_DIR.exists():
        print("Created installers:")
        for installer in INSTALLER_DIR.iterdir():
            if installer.is_file() and installer.suffix in ['.zip', '.gz', '.rpm', '.deb']:
                size_mb = installer.stat().st_size / 1024 / 1024
                print(f"  📦 {installer.name} ({size_mb:.2f} MB)")
    
    print("\n📝 To build for other platforms:")
    print("   1. Copy the entire agent folder to the target platform")
    print("   2. Run: python build_agent.py")
    print("   3. Copy the installer back to this machine")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Build cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Build error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)