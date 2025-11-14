#!/usr/bin/env python3
"""
Build Windows Installer (.exe) using Inno Setup
"""
import os
import sys
import subprocess
from pathlib import Path

def find_inno_setup():
    """Find Inno Setup compiler"""
    possible_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def build_installer():
    """Build the installer using Inno Setup"""
    print("🔨 Building Windows Installer (.exe)...")
    
    # Check if Inno Setup is installed
    iscc_path = find_inno_setup()
    
    if not iscc_path:
        print("\n❌ Inno Setup not found!")
        print("\n📥 Please install Inno Setup:")
        print("   1. Download from: https://jrsoftware.org/isdl.php")
        print("   2. Install (default location is fine)")
        print("   3. Run this script again\n")
        return False
    
    print(f"✓ Found Inno Setup: {iscc_path}")
    
    # Check if installer.iss exists
    script_file = Path("installer.iss")
    if not script_file.exists():
        print("❌ installer.iss not found!")
        return False
    
    # Check if dist/pci-agent.exe exists
    exe_file = Path("dist/pci-agent.exe")
    if not exe_file.exists():
        print("❌ dist/pci-agent.exe not found!")
        print("   Run 'python build_agent.py' first to build the executable")
        return False
    
    # Run Inno Setup compiler
    try:
        result = subprocess.run(
            [iscc_path, str(script_file)],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("✓ Installer compiled successfully!")
        print(f"\n📦 Output: installers\\pci-agent-installer-1.0.0.exe")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Compilation failed:")
        print(e.stderr)
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  PCI Compliance Agent - Installer Builder")
    print("=" * 60)
    print()
    
    if build_installer():
        print("\n✅ Done! You can now distribute:")
        print("   installers\\pci-agent-installer-1.0.0.exe")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)
