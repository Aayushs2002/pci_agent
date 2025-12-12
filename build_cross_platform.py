#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cross-Platform Build Script for PCI Compliance Agent
Builds Windows and Linux (RPM) packages from any platform using Docker
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import shutil
import json
from datetime import datetime

# Configure UTF-8 encoding for Windows console
if platform.system() == 'Windows':
    try:
        # Set console to UTF-8
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        # Python < 3.7 fallback
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')

VERSION = "1.0.0"
AGENT_NAME = "pci-compliance-agent"

def safe_print(text):
    """Print with fallback for environments that don't support Unicode"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Remove emoji and special characters
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text)

def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, 
                              text=True,
                              timeout=5)
        if result.returncode == 0:
            safe_print(f"[OK] Docker found: {result.stdout.strip()}")
            return True
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def build_windows_native():
    """Build Windows package natively"""
    safe_print("Building Windows package (native)...")
    
    try:
        # Use Python to run the build script
        result = subprocess.run(
            [sys.executable, "build_agent.py", "--platform", "windows"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            safe_print("  [OK] Windows build completed")
            return True
        else:
            safe_print("  [FAILED] Windows build failed")
            if result.stderr:
                safe_print(f"  Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  ✗ Windows build error: {e}")
        return False

def build_linux_docker():
    """Build Linux RPM package using Docker"""
    safe_print("Building Linux RPM package (Docker)...")
    
    agent_dir = Path(__file__).parent
    dockerfile = agent_dir / "Dockerfile.linux-builder"
    
    if not dockerfile.exists():
        safe_print("  [FAILED] Dockerfile.linux-builder not found")
        return False
    
    try:
        # Build Docker image
        safe_print("  Building Docker image...")
        build_cmd = [
            "docker", "build",
            "-f", str(dockerfile),
            "-t", "pci-agent-linux-builder",
            str(agent_dir)
        ]
        
        result = subprocess.run(build_cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        if result.returncode != 0:
            safe_print(f"  [FAILED] Docker image build failed:")
            safe_print(result.stderr)
            return False
        
        safe_print("  [OK] Docker image built")
        
        # Run build inside container
        safe_print("  Building agent in container...")
        
        # Create installers directory if it doesn't exist
        installers_dir = agent_dir / "installers"
        installers_dir.mkdir(parents=True, exist_ok=True)
        
        # Run container to build executable
        run_cmd = [
            "docker", "run",
            "--rm",
            "-v", f"{agent_dir}:/build",
            "pci-agent-linux-builder",
            "python3", "build_agent.py", "--platform", "linux"
        ]
        
        result = subprocess.run(run_cmd, capture_output=False, text=True, encoding='utf-8', errors='replace')
        
        if result.returncode != 0:
            safe_print("  [FAILED] Agent build failed in container")
            return False
        
        safe_print("  [OK] Agent executable built")
        
        # Now build RPM in container
        safe_print("  Building RPM package...")
        rpm_cmd = [
            "docker", "run",
            "--rm",
            "-v", f"{agent_dir}:/build",
            "pci-agent-linux-builder",
            "python3", "build_rpm.py"
        ]
        
        result = subprocess.run(rpm_cmd, capture_output=False, text=True, encoding='utf-8', errors='replace')
        
        if result.returncode != 0:
            safe_print("  [FAILED] RPM build failed")
            return False
        
        safe_print("  [OK] Linux RPM build completed")
        return True
        
    except Exception as e:
        safe_print(f"  [FAILED] Docker build error: {e}")
        return False

def build_linux_tarball_docker():
    """Build Linux TAR.GZ package using Docker (fallback if RPM fails)"""
    safe_print("Building Linux TAR.GZ package (Docker)...")
    
    agent_dir = Path(__file__).parent
    dockerfile = agent_dir / "Dockerfile.linux-builder"
    
    try:
        # Build Docker image if not already built
        safe_print("  Preparing Docker image...")
        build_cmd = [
            "docker", "build",
            "-f", str(dockerfile),
            "-t", "pci-agent-linux-builder",
            str(agent_dir)
        ]
        subprocess.run(build_cmd, capture_output=True, check=False, encoding='utf-8', errors='replace')
        
        # Run build inside container
        safe_print("  Building TAR.GZ package...")
        run_cmd = [
            "docker", "run",
            "--rm",
            "-v", f"{agent_dir}:/build",
            "pci-agent-linux-builder",
            "python3", "build_agent.py", "--platform", "linux"
        ]
        
        result = subprocess.run(run_cmd, capture_output=False, encoding='utf-8', errors='replace')
        
        if result.returncode == 0:
            safe_print("  [OK] Linux TAR.GZ build completed")
            return True
        else:
            safe_print("  [FAILED] TAR.GZ build failed")
            return False
            
    except Exception as e:
        safe_print(f"  [FAILED] Docker build error: {e}")
        return False

def create_combined_metadata():
    """Create metadata file for all installers"""
    safe_print("\nCreating installer metadata...")
    
    installer_dir = Path(__file__).parent / "installers"
    if not installer_dir.exists():
        safe_print("  Warning: No installers directory found")
        return
    
    metadata = {
        "name": AGENT_NAME,
        "version": VERSION,
        "build_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "build_platform": platform.system(),
        "installers": []
    }
    
    # List all installers
    for installer_file in installer_dir.iterdir():
        if installer_file.is_file() and installer_file.suffix in ['.zip', '.gz', '.rpm']:
            # Determine platform
            if 'windows' in installer_file.name.lower():
                plat = 'windows'
            elif 'linux' in installer_file.name.lower():
                plat = 'linux'
            else:
                plat = 'unknown'
            
            # Determine type
            if installer_file.suffix == '.rpm':
                pkg_type = 'rpm'
            elif installer_file.suffix == '.gz':
                pkg_type = 'tar.gz'
            elif installer_file.suffix == '.zip':
                pkg_type = 'zip'
            else:
                pkg_type = 'unknown'
            
            metadata["installers"].append({
                "filename": installer_file.name,
                "platform": plat,
                "type": pkg_type,
                "size": installer_file.stat().st_size,
                "size_mb": round(installer_file.stat().st_size / 1024 / 1024, 2)
            })
    
    # Save metadata
    metadata_file = installer_dir / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2))
    safe_print(f"  [OK] Created: {metadata_file.name}")

def print_summary():
    """Print build summary"""
    safe_print("\n" + "="*60)
    safe_print("Build Summary")
    safe_print("="*60)
    
    installer_dir = Path(__file__).parent / "installers"
    if not installer_dir.exists():
        print("No installers created")
        return
    
    installers = sorted(installer_dir.glob("*.*"))
    installers = [f for f in installers if f.suffix in ['.zip', '.gz', '.rpm']]
    
    if not installers:
        print("No installers found")
        return
    
    for installer in installers:
        size_mb = installer.stat().st_size / 1024 / 1024
        icon = "[WIN]" if "windows" in installer.name.lower() else "[LNX]"
        safe_print(f"{icon} {installer.name:50s} {size_mb:>8.2f} MB")
    
    print("")
    print("Installation Instructions:")
    print("")
    print("Windows:")
    print("  1. Download the .zip file")
    print("  2. Extract and run install.bat as Administrator")
    print("")
    print("Linux (RPM - CentOS/RHEL/Fedora):")
    print("  sudo rpm -ivh pci-compliance-agent-*.rpm")
    print("  sudo systemctl start pci-agent")
    print("")
    print("Linux (TAR.GZ - All distributions):")
    print("  tar -xzf pci-compliance-agent-*.tar.gz")
    print("  cd pci-compliance-agent-*/")
    print("  sudo ./install.sh")
    print("")

def main(skip_confirm=False):
    """Main build orchestrator"""
    safe_print("=" * 60)
    safe_print("PCI Compliance Agent - Cross-Platform Builder")
    safe_print(f"Version: {VERSION}")
    safe_print(f"Host Platform: {platform.system()}")
    safe_print("=" * 60)
    safe_print("")
    
    # Determine what to build
    current_platform = platform.system()
    has_docker = check_docker()
    
    safe_print("")
    safe_print("Build Plan:")
    safe_print(f"  - Windows Package: {'Native build' if current_platform == 'Windows' else 'Not available (run on Windows)'}")
    safe_print(f"  - Linux RPM Package: {'Docker build' if has_docker else 'Not available (Docker required)'}")
    safe_print("")
    
    if not has_docker and current_platform != 'Windows':
        safe_print("Warning: Docker not found. Can only build for current platform.")
        safe_print("   Install Docker to enable cross-platform builds.")
        safe_print("")
    
    # Confirm (skip if automated)
    if not skip_confirm:
        try:
            response = input("Continue with build? [Y/n]: ").strip().lower()
            if response and response not in ['y', 'yes']:
                safe_print("Build cancelled")
                return False
        except KeyboardInterrupt:
            safe_print("\nBuild cancelled")
            return False
    else:
        safe_print("Auto-build mode: Skipping confirmation")
    
    safe_print("")
    success_count = 0
    total_builds = 0
    
    # Build Windows (if on Windows)
    if current_platform == 'Windows':
        total_builds += 1
        if build_windows_native():
            success_count += 1
    
    # Build Linux with Docker
    if has_docker:
        total_builds += 1
        linux_success = build_linux_docker()
        if not linux_success:
            # Fallback to TAR.GZ if RPM fails
            safe_print("\nRPM build failed, trying TAR.GZ fallback...")
            linux_success = build_linux_tarball_docker()
        
        if linux_success:
            success_count += 1
    
    # Create metadata
    create_combined_metadata()
    
    # Print summary
    print_summary()
    
    # Final status
    safe_print("="*60)
    if success_count == total_builds and total_builds > 0:
        safe_print("SUCCESS: All builds completed successfully!")
    elif success_count > 0:
        safe_print(f"PARTIAL: {success_count}/{total_builds} builds completed")
    else:
        safe_print("FAILED: Build failed")
    safe_print("="*60)
    safe_print("")
    
    return success_count > 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Build PCI Compliance Agent for multiple platforms')
    parser.add_argument('--skip-confirm', '-y', action='store_true', 
                       help='Skip confirmation prompt (for automated builds)')
    parser.add_argument('--version', action='version', version=f'{AGENT_NAME} {VERSION}')
    
    args = parser.parse_args()
    
    try:
        success = main(skip_confirm=args.skip_confirm)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        safe_print("\n\nBuild cancelled by user")
        sys.exit(130)
    except Exception as e:
        safe_print(f"\nBuild error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
