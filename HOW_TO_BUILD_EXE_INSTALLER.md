# Creating a Windows .EXE Installer

You have **3 options** to create a Windows installer executable:

## Option 1: Inno Setup (Most Professional) ✨

**Best for:** Production deployment, professional appearance

### Steps:

1. **Install Inno Setup**
   - Download from: https://jrsoftware.org/isdl.php
   - Run the installer (use default options)

2. **Build the agent first**
   ```powershell
   cd E:\personalProject\pci-compliane\pci-compliance-agent
   python build_agent.py
   ```

3. **Build the .exe installer**
   ```powershell
   python build_installer_exe.py
   ```

4. **Result:**
   - Output: `installers\pci-agent-installer-1.0.0.exe`
   - Professional Windows installer
   - Creates Start Menu shortcuts
   - Proper uninstaller
   - ~70 MB file size

### Features:
- ✅ Professional Windows installer UI
- ✅ Start Menu integration
- ✅ Desktop shortcut (optional)
- ✅ Proper uninstall support
- ✅ Administrator privilege handling
- ✅ Custom installation directory
- ✅ Configuration editor shortcut

---

## Option 2: 7-Zip SFX (Self-Extracting) 📦

**Best for:** Quick distribution without extra software

### Steps:

1. **Install 7-Zip**
   - Download from: https://www.7-zip.org/download.html
   - Run the installer

2. **Build the agent first**
   ```powershell
   cd E:\personalProject\pci-compliane\pci-compliance-agent
   python build_agent.py
   ```

3. **Build the SFX installer**
   ```powershell
   python build_sfx_installer.py
   ```

4. **Result:**
   - Output: `installers\pci-agent-installer-1.0.0.exe`
   - Self-extracting archive
   - Automatically runs install.bat
   - ~70 MB file size

### Features:
- ✅ Simple to create
- ✅ No external dependencies after creation
- ✅ Runs installation script automatically
- ❌ Less professional looking
- ❌ No uninstaller (manual removal only)

---

## Option 3: Simple Rename (Quickest) 🚀

**Best for:** Testing, internal use

### Steps:

1. **Build the agent**
   ```powershell
   cd E:\personalProject\pci-compliane\pci-compliance-agent
   python build_agent.py
   ```

2. **Rename the ZIP file**
   ```powershell
   cd installers
   Copy-Item pci-compliance-agent-1.0.0-windows-x64.zip pci-agent-installer-1.0.0.exe
   ```

3. **Result:**
   - The .exe file is actually a ZIP
   - Windows can extract it when double-clicked
   - User sees files and runs install.bat
   - ~70 MB file size

### Features:
- ✅ Instant - no extra software needed
- ✅ Works immediately
- ❌ Not a "real" installer
- ❌ User must extract and run install.bat manually
- ⚠️ Windows SmartScreen warning (expected for unsigned)

---

## Comparison Table

| Feature | Inno Setup | 7-Zip SFX | Rename Method |
|---------|-----------|-----------|---------------|
| Professional UI | ✅ | ❌ | ❌ |
| One-click install | ✅ | ⚠️ Semi | ❌ |
| Start Menu shortcuts | ✅ | ❌ | ❌ |
| Proper uninstaller | ✅ | ❌ | ❌ |
| Easy to create | ⚠️ Requires software | ⚠️ Requires 7-Zip | ✅ Instant |
| File size | ~70 MB | ~70 MB | ~70 MB |
| Signed installer | ⚠️ Needs code signing | ⚠️ Needs code signing | ⚠️ Needs code signing |

---

## Recommended Approach

### For Production:
**Use Inno Setup** - Most professional, best user experience

```powershell
# One-time setup
# 1. Download and install Inno Setup from https://jrsoftware.org/isdl.php

# Every build
cd E:\personalProject\pci-compliane\pci-compliance-agent
python build_agent.py
python build_installer_exe.py
```

### For Quick Testing:
**Use Simple Rename** - Instant, no dependencies

```powershell
cd E:\personalProject\pci-compliane\pci-compliance-agent
python build_agent.py
cd installers
Copy-Item pci-compliance-agent-1.0.0-windows-x64.zip pci-agent-installer-1.0.0.exe
```

---

## Current Status

✅ **Already created:**
- `build_installer_exe.py` - Builds Inno Setup installer
- `build_sfx_installer.py` - Builds 7-Zip SFX installer
- `installer.iss` - Inno Setup script
- `build_agent.py` - Main build script (creates ZIP)

✅ **What you have now:**
- `installers\pci-compliance-agent-1.0.0-windows-x64.zip` (68.31 MB)

---

## Next Steps

Choose one of these commands:

### Option 1: Install Inno Setup and build professional installer
```powershell
# After installing Inno Setup from https://jrsoftware.org/isdl.php
python build_installer_exe.py
```

### Option 2: Install 7-Zip and build SFX installer
```powershell
# After installing 7-Zip from https://www.7-zip.org/
python build_sfx_installer.py
```

### Option 3: Quick rename (no install needed)
```powershell
cd installers
Copy-Item pci-compliance-agent-1.0.0-windows-x64.zip pci-agent-installer.exe
```

**⚠️ IMPORTANT:** This creates an `.exe` that is actually a ZIP file. Users need to:
1. **Right-click** the `.exe` file
2. Choose **"Extract All..."** or **"Open with" → "Windows Explorer"**
3. Extract the files to a folder
4. Open the extracted folder
5. Right-click **`install.bat`** → **"Run as Administrator"**

This is NOT a true executable installer - it's just a ZIP with an .exe extension!

---

## Code Signing (Optional but Recommended)

To avoid Windows SmartScreen warnings, you should sign the installer:

1. **Get a code signing certificate** ($100-$500/year)
   - From: DigiCert, Sectigo, GlobalSign, etc.

2. **Sign the installer**
   ```powershell
   signtool sign /f your-certificate.pfx /p password /t http://timestamp.digicert.com installers\pci-agent-installer-1.0.0.exe
   ```

Without signing, users will see:
- "Windows protected your PC" warning
- They need to click "More info" → "Run anyway"
- This is normal for unsigned software

---

## Questions?

Let me know which method you want to use and I'll help you set it up!
