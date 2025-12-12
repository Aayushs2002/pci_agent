# Cross-Platform Agent Building Guide

Build PCI Compliance Agent installers for **Windows** and **Linux (RPM)** from your Windows machine.

---

## 🎯 What You'll Get

After building, you'll have:

- ✅ **Windows Installer** (.zip) - Native Windows build
- ✅ **Linux RPM Package** (.rpm) - For CentOS/RHEL/Fedora
- ✅ **Linux TAR.GZ** (.tar.gz) - For all Linux distributions

---

## 📋 Prerequisites

### For Windows Builds (Native)
- ✅ Python 3.8+ installed
- ✅ pip package manager
- ✅ Windows 10/11

### For Linux Builds (Docker)
- ✅ **Docker Desktop** installed and running
- ✅ At least 2GB free disk space
- ✅ Internet connection (for Docker image download)

---

## 🚀 Quick Start

### Option 1: GUI Build (Recommended)

1. **Open the Web GUI** at `http://localhost:3000`
2. Navigate to **"Deployment"** tab
3. Click **"Build Installers"** button
4. Wait 3-5 minutes for build completion
5. Download installers when ready

### Option 2: Command Line Build

```bash
cd pci-compliance-agent
python build_cross_platform.py
```

This will automatically:
- ✅ Build Windows installer (native)
- ✅ Build Linux RPM package (Docker)
- ✅ Create both packages in `installers/` directory

---

## 📦 Manual Build Steps

### Step 1: Install Docker Desktop (One-Time Setup)

#### Windows
1. Download Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Install and restart your computer
3. Launch Docker Desktop
4. Wait for Docker to start (icon in system tray will turn green)

#### Verify Docker Installation
```powershell
docker --version
# Should show: Docker version 24.x.x or higher
```

### Step 2: Build Windows Installer (Native)

```powershell
cd pci-compliance-agent
python build_agent.py --platform windows
```

Output: `installers/pci-compliance-agent-1.0.0-windows-x64.zip`

### Step 3: Build Linux RPM Package (Docker)

```powershell
# This uses Docker to build on a Linux container
python build_cross_platform.py
```

Output: 
- `installers/pci-compliance-agent-1.0.0-1.x86_64.rpm` (RPM package)
- `installers/pci-compliance-agent-1.0.0-linux-x64.tar.gz` (TAR.GZ fallback)

---

## 🐳 Docker Build Process Explained

The cross-platform builder:

1. **Creates CentOS 8 Docker image** with build tools
2. **Compiles Python agent** inside Linux container
3. **Builds RPM package** using `rpmbuild`
4. **Copies installer** back to Windows host
5. **Cleans up** Docker containers

**Total time:** 3-5 minutes (first build), 1-2 minutes (subsequent builds)

---

## 📂 Output Files

All installers are created in:
```
pci-compliance-agent/installers/
```

### Windows Package
```
pci-compliance-agent-1.0.0-windows-x64.zip
  ├── pci-agent.exe           (Standalone executable)
  ├── config.yaml             (Configuration file)
  ├── install.bat             (Installation script)
  ├── launcher.bat            (Easy launcher with menu)
  └── README.txt              (Instructions)
```

### Linux RPM Package
```
pci-compliance-agent-1.0.0-1.x86_64.rpm
  
  Contents (installed via RPM):
  ├── /usr/local/bin/pci-agent              (Executable)
  ├── /etc/pci-compliance-agent/config.yaml (Config)
  ├── /usr/lib/systemd/system/pci-agent.service (Service)
  └── /var/log/pci-compliance-agent/        (Logs directory)
```

### Linux TAR.GZ Package
```
pci-compliance-agent-1.0.0-linux-x64.tar.gz
  ├── pci-agent               (Standalone executable)
  ├── config.yaml             (Configuration file)
  ├── install.sh              (Installation script)
  └── pci-agent.service       (Systemd service file)
```

---

## 🎯 Installation Instructions

### Windows Installation

```powershell
# 1. Extract ZIP file
Expand-Archive pci-compliance-agent-1.0.0-windows-x64.zip

# 2. Run installer as Administrator
cd pci-compliance-agent-1.0.0
.\install.bat
```

### Linux RPM Installation (CentOS/RHEL/Fedora)

```bash
# Install the package
sudo rpm -ivh pci-compliance-agent-1.0.0-1.x86_64.rpm

# Configure
sudo nano /etc/pci-compliance-agent/config.yaml

# Start service
sudo systemctl start pci-agent
sudo systemctl enable pci-agent

# Check status
sudo systemctl status pci-agent
```

### Linux TAR.GZ Installation (All Distributions)

```bash
# Extract
tar -xzf pci-compliance-agent-1.0.0-linux-x64.tar.gz
cd pci-compliance-agent-1.0.0

# Install
sudo ./install.sh

# Configure
sudo nano /etc/pci-compliance-agent/config.yaml

# Start service
sudo systemctl start pci-agent
sudo systemctl enable pci-agent
```

---

## 🔧 Troubleshooting

### Docker Not Running

**Error:** `Cannot connect to Docker daemon`

**Solution:**
1. Open Docker Desktop
2. Wait for it to fully start (green icon in system tray)
3. Try build again

### Build Fails with "Permission Denied"

**Solution:**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Linux Build Fails

**Solution:**
```powershell
# Clean Docker cache
docker system prune -a

# Rebuild from scratch
python build_cross_platform.py
```

### RPM Build Skipped

If RPM build fails, the system automatically falls back to TAR.GZ format.
This is normal and both formats work on Linux.

---

## ⚙️ Advanced Configuration

### Build Only Windows

```powershell
python build_agent.py --platform windows
```

### Build Only Linux

```powershell
python build_agent.py --platform linux
```

### Custom Docker Image

Edit `Dockerfile.linux-builder` to customize the Linux build environment.

### Skip Executable Build

If you already have the executable:
```powershell
python build_agent.py --skip-build
```

---

## 📊 Build Performance

| Platform | Method | Time | Size |
|----------|--------|------|------|
| Windows | Native | ~2 min | ~15 MB |
| Linux RPM | Docker | ~5 min | ~18 MB |
| Linux TAR.GZ | Docker | ~3 min | ~16 MB |

**Note:** First Docker build takes longer due to image download.

---

## 🔐 Security Notes

### Windows Builds
- Executables are **not signed** by default
- Some antivirus may flag unsigned executables
- To distribute, consider code signing

### Linux Builds
- RPM packages can be GPG signed
- TAR.GZ should be distributed over HTTPS
- Verify checksums after download

---

## 📝 Metadata File

After building, a `metadata.json` file is created:

```json
{
  "name": "pci-compliance-agent",
  "version": "1.0.0",
  "build_date": "2025-11-18 12:30:00",
  "build_platform": "Windows",
  "installers": [
    {
      "filename": "pci-compliance-agent-1.0.0-windows-x64.zip",
      "platform": "windows",
      "type": "zip",
      "size_mb": 14.5
    },
    {
      "filename": "pci-compliance-agent-1.0.0-1.x86_64.rpm",
      "platform": "linux",
      "type": "rpm",
      "size_mb": 17.8
    }
  ]
}
```

This metadata is used by the GUI deployment interface.

---

## 🚀 CI/CD Integration

### GitHub Actions Example

```yaml
name: Build Agents

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: python build_agent.py --platform windows
      - uses: actions/upload-artifact@v3
        with:
          name: windows-installer
          path: installers/*.zip

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: python build_rpm.py
      - uses: actions/upload-artifact@v3
        with:
          name: linux-installer
          path: installers/*.rpm
```

---

## 📞 Support

- **Documentation:** See `BUILD_LINUX.md` for detailed Linux instructions
- **Issues:** Report problems on GitHub
- **Docker Help:** https://docs.docker.com/desktop/

---

## ✅ Checklist

Before building:
- [ ] Python 3.8+ installed
- [ ] Docker Desktop installed (for Linux builds)
- [ ] Docker Desktop is running
- [ ] Internet connection available
- [ ] At least 2GB free disk space

After building:
- [ ] Check `installers/` directory
- [ ] Verify file sizes are reasonable
- [ ] Test Windows installer on Windows machine
- [ ] Test Linux installer on Linux machine
- [ ] Update deployment documentation

---

## 🎉 Success!

You should now have installers for both Windows and Linux ready to deploy!

Upload them to your deployment server or distribute them to target machines.

---

**Last Updated:** November 2025  
**Version:** 1.0.0
