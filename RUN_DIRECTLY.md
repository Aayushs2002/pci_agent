# Running pci-agent.exe Directly (Without .bat file)

## ✅ Now you can just DOUBLE-CLICK pci-agent.exe!

The agent has been rebuilt with WebSocket mode enabled by default in the configuration.

## 🎯 Three Ways to Run the Agent

### Method 1: Direct Double-Click (NEW!)
```
Just double-click: pci-agent.exe
✓ Connects to http://localhost:3001 automatically
✓ No command-line arguments needed
```

### Method 2: Command Line with Arguments (Override defaults)
```powershell
.\pci-agent.exe --server-url http://192.168.1.100:3001
```

### Method 3: Desktop Shortcut
```
1. Run: CREATE_SHORTCUT.bat
2. A shortcut will be created on your desktop
3. Double-click the shortcut to run the agent
```

## 📋 Configuration

The agent now has these settings in `config.yaml`:

```yaml
reporting:
  server_url: "http://localhost:3001"
  websocket_url: "http://localhost:3001"
  websocket_mode: true  # ← Enabled by default!
```

## 🔄 How It Works

When you double-click `pci-agent.exe`:

1. ✓ Reads `config.yaml` (embedded in exe)
2. ✓ Sees `websocket_mode: true`
3. ✓ Automatically connects to `http://localhost:3001`
4. ✓ Registers with server
5. ✓ Waits for remote commands from GUI

## 🛠️ Command-Line Options (Optional)

You can still override settings via command line:

```powershell
# Use different server
.\pci-agent.exe --server-url http://192.168.1.50:3001

# Force CLI mode (disable WebSocket)
.\pci-agent.exe --operator "John" --directories "C:\temp" --no-send

# Verbose logging
.\pci-agent.exe --verbose
```

## 📍 File Locations

After extraction, you'll find:
```
pci-compliance-agent-1.0.0-windows-x64/
├── pci-agent.exe          ← Just double-click this!
├── config.yaml            ← Configuration (websocket_mode: true)
├── START_AGENT.bat        ← Alternative launcher
├── launcher.bat           ← Interactive menu
└── CREATE_SHORTCUT.bat    ← Creates desktop shortcut
```

## ✨ Summary

**OLD WAY (Required .bat file):**
```
Double-click START_AGENT.bat → Runs with arguments → Connects to server
```

**NEW WAY (Direct .exe):**
```
Double-click pci-agent.exe → Reads config.yaml → Connects to server
```

No batch file needed anymore! 🎉
