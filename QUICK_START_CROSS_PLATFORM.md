# Quick Start: Build Windows + Linux RPM from Windows

## Step 1: Install Docker Desktop (One-Time)

1. Download: https://www.docker.com/products/docker-desktop/
2. Install and restart computer
3. Launch Docker Desktop - wait for it to start (green icon)

## Step 2: Build All Platforms

```powershell
cd pci-compliance-agent
python build_cross_platform.py
```

**Wait 3-5 minutes...**

## Step 3: Get Your Installers

Check `installers/` folder:
- ✅ `pci-compliance-agent-1.0.0-windows-x64.zip` - Windows
- ✅ `pci-compliance-agent-1.0.0-1.x86_64.rpm` - Linux RPM

## Installation

### Windows
```powershell
# Extract and run install.bat as Administrator
```

### Linux (CentOS/RHEL/Fedora)
```bash
sudo rpm -ivh pci-compliance-agent-1.0.0-1.x86_64.rpm
sudo systemctl start pci-agent
```

---

## Alternative: Build from GUI

1. Open browser: `http://localhost:3000`
2. Go to **Deployment** tab
3. Click **"Build Installers"**
4. Download installers when ready

---

## Troubleshooting

**Docker not running?**
- Open Docker Desktop and wait for green icon

**Build fails?**
- Run PowerShell as Administrator
- Check Docker is running

**Need help?**
- See `CROSS_PLATFORM_BUILD.md` for detailed guide
- See `BUILD_LINUX.md` for Linux-specific instructions

---

That's it! You now have installers for both Windows and Linux (RPM). 🎉
