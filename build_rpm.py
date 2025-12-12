#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPM Package Builder for PCI Compliance Agent
Creates RPM packages for Red Hat/CentOS/Fedora systems
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import tempfile

VERSION = "1.0.0"
RELEASE = "1"
AGENT_NAME = "pci-compliance-agent"

def create_rpm_spec_file(build_root):
    """Create RPM spec file"""
    spec_content = f"""
Name:           {AGENT_NAME}
Version:        {VERSION}
Release:        {RELEASE}%{{?dist}}
Summary:        PCI DSS Compliance Scanner Agent

License:        Proprietary
URL:            https://github.com/your-org/pci-compliance-agent
Source0:        %{{name}}-%{{version}}.tar.gz

BuildArch:      x86_64
Requires:       systemd

%description
PCI DSS compliance scanning agent that detects payment card numbers
and sensitive data in files and systems. Provides real-time scanning,
reporting, and integration with central management server.

%prep
%setup -q

%build
# Binary already built with PyInstaller

%install
rm -rf $RPM_BUILD_ROOT

# Create directory structure
mkdir -p $RPM_BUILD_ROOT/usr/local/bin
mkdir -p $RPM_BUILD_ROOT/etc/%{{name}}
mkdir -p $RPM_BUILD_ROOT/var/log/%{{name}}
mkdir -p $RPM_BUILD_ROOT/var/lib/%{{name}}/reports
mkdir -p $RPM_BUILD_ROOT/usr/lib/systemd/system
mkdir -p $RPM_BUILD_ROOT/usr/share/doc/%{{name}}

# Install files
install -m 755 pci-agent $RPM_BUILD_ROOT/usr/local/bin/
install -m 644 config.yaml $RPM_BUILD_ROOT/etc/%{{name}}/
install -m 644 pci-agent.service $RPM_BUILD_ROOT/usr/lib/systemd/system/
install -m 644 README.txt $RPM_BUILD_ROOT/usr/share/doc/%{{name}}/

%clean
rm -rf $RPM_BUILD_ROOT

%pre
# Create user if it doesn't exist
getent group pciagent >/dev/null || groupadd -r pciagent
getent passwd pciagent >/dev/null || useradd -r -g pciagent -d /var/lib/%{{name}} -s /sbin/nologin -c "PCI Compliance Agent" pciagent

%post
# Set permissions
chown -R pciagent:pciagent /var/log/%{{name}}
chown -R pciagent:pciagent /var/lib/%{{name}}
chmod 750 /var/log/%{{name}}
chmod 750 /var/lib/%{{name}}

# Reload systemd
systemctl daemon-reload

echo "PCI Compliance Agent installed successfully!"
echo "To configure: sudo nano /etc/%{{name}}/config.yaml"
echo "To start: sudo systemctl start pci-agent"
echo "To enable on boot: sudo systemctl enable pci-agent"

%preun
# Stop service before uninstall
if [ $1 -eq 0 ]; then
    systemctl stop pci-agent 2>/dev/null || true
    systemctl disable pci-agent 2>/dev/null || true
fi

%postun
# Cleanup after uninstall
if [ $1 -eq 0 ]; then
    systemctl daemon-reload
    # Optionally remove user/group
    # userdel pciagent 2>/dev/null || true
fi

%files
%defattr(-,root,root,-)
/usr/local/bin/pci-agent
%config(noreplace) /etc/%{{name}}/config.yaml
/usr/lib/systemd/system/pci-agent.service
/usr/share/doc/%{{name}}/README.txt
%attr(750,pciagent,pciagent) /var/log/%{{name}}
%attr(750,pciagent,pciagent) /var/lib/%{{name}}
%attr(750,pciagent,pciagent) /var/lib/%{{name}}/reports

%changelog
* {subprocess.check_output(['date', '+%a %b %d %Y'], text=True, stderr=subprocess.DEVNULL).strip() if sys.platform != 'win32' else 'Mon Jan 01 2024'} Builder <builder@example.com> - {VERSION}-{RELEASE}
- Initial RPM package
"""
    
    spec_file = build_root / f"{AGENT_NAME}.spec"
    spec_file.write_text(spec_content)
    return spec_file

def build_rpm_package(exe_path):
    """Build RPM package using rpmbuild"""
    print("🔨 Building RPM package...")
    
    # Create temporary build structure
    with tempfile.TemporaryDirectory() as tmpdir:
        build_root = Path(tmpdir) / "rpmbuild"
        
        # Create rpmbuild directory structure
        for subdir in ['BUILD', 'RPMS', 'SOURCES', 'SPECS', 'SRPMS']:
            (build_root / subdir).mkdir(parents=True)
        
        # Create source tarball structure
        source_dir = build_root / "BUILD" / f"{AGENT_NAME}-{VERSION}"
        source_dir.mkdir(parents=True)
        
        # Copy executable
        shutil.copy(exe_path, source_dir / "pci-agent")
        os.chmod(source_dir / "pci-agent", 0o755)
        
        # Copy config
        config_src = Path(__file__).parent / "config.example.yaml"
        shutil.copy(config_src, source_dir / "config.yaml")
        
        # Create systemd service file
        service_content = """[Unit]
Description=PCI Compliance Agent
After=network.target

[Service]
Type=simple
User=pciagent
Group=pciagent
WorkingDirectory=/etc/pci-compliance-agent
ExecStart=/usr/local/bin/pci-agent --websocket-mode --server-url http://192.168.56.1:3001
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        (source_dir / "pci-agent.service").write_text(service_content)
        
        # Create README
        readme_content = f"""PCI Compliance Agent v{VERSION}
================================

Configuration File: /etc/pci-compliance-agent/config.yaml
Log Directory: /var/log/pci-compliance-agent/
Reports Directory: /var/lib/pci-compliance-agent/reports/

Quick Start:
1. Edit configuration: sudo nano /etc/pci-compliance-agent/config.yaml
2. Update server_url to your management server
3. Start service: sudo systemctl start pci-agent
4. Enable on boot: sudo systemctl enable pci-agent
5. Check status: sudo systemctl status pci-agent

For more information, visit: https://github.com/your-org/pci-compliance-agent
"""
        (source_dir / "README.txt").write_text(readme_content)
        
        # Create spec file
        spec_file = create_rpm_spec_file(build_root / "SPECS")
        
        # Create source tarball
        import tarfile
        source_tarball = build_root / "SOURCES" / f"{AGENT_NAME}-{VERSION}.tar.gz"
        with tarfile.open(source_tarball, "w:gz") as tar:
            tar.add(source_dir, arcname=f"{AGENT_NAME}-{VERSION}")
        
        print(f"  ✓ Created source tarball: {source_tarball.name}")
        
        # Build RPM
        try:
            cmd = [
                "rpmbuild",
                "-ba",
                "--define", f"_topdir {build_root}",
                str(spec_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Find the created RPM
                rpm_dir = build_root / "RPMS" / "x86_64"
                if rpm_dir.exists():
                    rpms = list(rpm_dir.glob("*.rpm"))
                    if rpms:
                        # Copy RPM to installers directory
                        installer_dir = Path(__file__).parent / "installers"
                        installer_dir.mkdir(parents=True, exist_ok=True)
                        
                        rpm_file = rpms[0]
                        dest = installer_dir / rpm_file.name
                        shutil.copy(rpm_file, dest)
                        
                        print(f"  ✓ RPM package created: {dest.name}")
                        print(f"  📦 Size: {dest.stat().st_size / 1024 / 1024:.2f} MB")
                        return dest
                    else:
                        print("  ✗ No RPM file found in output")
                        return None
                else:
                    print(f"  ✗ RPM directory not found: {rpm_dir}")
                    return None
            else:
                print(f"  ✗ RPM build failed:")
                print(result.stderr)
                return None
                
        except FileNotFoundError:
            print("  ✗ rpmbuild not found. Install rpm-build package:")
            print("     sudo yum install rpm-build  (CentOS/RHEL)")
            print("     sudo dnf install rpm-build  (Fedora)")
            return None
        except Exception as e:
            print(f"  ✗ RPM build error: {e}")
            return None

def main():
    """Main RPM build process"""
    print(f"📦 RPM Package Builder for {AGENT_NAME} v{VERSION}")
    print("")
    
    # Check if we're on Linux
    if sys.platform != 'linux':
        print("❌ RPM building is only supported on Linux")
        print("   Please use Docker or run this on a Linux machine")
        return False
    
    # Find the executable
    exe_path = Path("dist") / "pci-agent" / "pci-agent"
    if not exe_path.exists():
        exe_path = Path("dist") / "pci-agent"
    
    if not exe_path.exists():
        print("❌ Executable not found. Please build it first:")
        print("   python build_agent.py")
        return False
    
    print(f"✓ Found executable: {exe_path}")
    
    # Build RPM
    rpm_path = build_rpm_package(exe_path)
    
    if rpm_path:
        print("")
        print("✅ RPM package built successfully!")
        print(f"📂 Location: {rpm_path}")
        print("")
        print("To install:")
        print(f"  sudo rpm -ivh {rpm_path.name}")
        print("")
        print("To upgrade:")
        print(f"  sudo rpm -Uvh {rpm_path.name}")
        print("")
        return True
    else:
        print("")
        print("❌ RPM build failed")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Build cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
