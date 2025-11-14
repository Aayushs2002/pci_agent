#!/usr/bin/env python3
"""
Build Self-Extracting Windows Installer (.exe)
This creates a simple .exe installer using 7-Zip SFX
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def find_7zip():
    """Find 7-Zip executable"""
    possible_paths = [
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def create_sfx_config():
    """Create 7-Zip SFX configuration"""
    config = """
;!@Install@!UTF-8!
Title="PCI Compliance Agent Installer"
BeginPrompt="This will install PCI Compliance Agent v1.0.0\\n\\nClick OK to continue."
RunProgram="install.bat"
;!@InstallEnd@!
"""
    Path("installers").mkdir(exist_ok=True)
    with open("installers/sfx_config.txt", "w", encoding="utf-8") as f:
        f.write(config)

def build_sfx_installer():
    """Build self-extracting installer"""
    print("🔨 Building Self-Extracting Installer (.exe)...")
    
    # Check if 7-Zip is installed
    zip7_path = find_7zip()
    
    if not zip7_path:
        print("\n❌ 7-Zip not found!")
        print("\n📥 Please install 7-Zip:")
        print("   1. Download from: https://www.7-zip.org/download.html")
        print("   2. Install (default location is fine)")
        print("   3. Run this script again\n")
        print("   OR use the simpler method: Just rename the ZIP to .exe")
        return False
    
    print(f"✓ Found 7-Zip: {zip7_path}")
    
    # Check if package exists
    package_dir = Path("build_temp/windows_package")
    if not package_dir.exists():
        print("❌ Windows package not found!")
        print("   Run 'python build_agent.py' first")
        return False
    
    # Create SFX config
    create_sfx_config()
    
    # Create 7z archive
    print("  Creating archive...")
    archive_path = Path("installers/pci-agent-temp.7z")
    try:
        subprocess.run(
            [zip7_path, "a", "-t7z", str(archive_path), f"{package_dir}/*"],
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create archive: {e}")
        return False
    
    # Find 7z SFX module
    sfx_module = Path(zip7_path).parent / "7z.sfx"
    if not sfx_module.exists():
        sfx_module = Path(zip7_path).parent / "7zS.sfx"
    
    if not sfx_module.exists():
        print("❌ 7-Zip SFX module not found!")
        return False
    
    # Combine SFX module + config + archive
    print("  Creating self-extracting executable...")
    output_exe = Path("installers/pci-agent-installer-1.0.0.exe")
    
    try:
        with open(output_exe, "wb") as outfile:
            # SFX module
            with open(sfx_module, "rb") as f:
                outfile.write(f.read())
            # Config
            with open("installers/sfx_config.txt", "rb") as f:
                outfile.write(f.read())
            # Archive
            with open(archive_path, "rb") as f:
                outfile.write(f.read())
        
        # Clean up temp files
        archive_path.unlink()
        Path("installers/sfx_config.txt").unlink()
        
        print("✓ Self-extracting installer created!")
        print(f"\n📦 Output: {output_exe}")
        print(f"   Size: {output_exe.stat().st_size / 1024 / 1024:.2f} MB")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create installer: {e}")
        return False

def simple_rename_method():
    """Simple method: Just rename ZIP to .exe"""
    print("\n💡 SIMPLE METHOD:")
    print("   You can just rename the ZIP file to .exe:")
    print("   1. Find: installers/pci-compliance-agent-1.0.0-windows-x64.zip")
    print("   2. Rename to: pci-compliance-agent-installer-1.0.0.exe")
    print("   3. Users double-click it, it extracts and runs install.bat")
    print("   4. Windows will show a security warning (normal for unsigned installers)")

if __name__ == "__main__":
    print("=" * 60)
    print("  PCI Compliance Agent - SFX Installer Builder")
    print("=" * 60)
    print()
    
    if build_sfx_installer():
        print("\n✅ Done! You can now distribute:")
        print("   installers/pci-agent-installer-1.0.0.exe")
    else:
        simple_rename_method()
