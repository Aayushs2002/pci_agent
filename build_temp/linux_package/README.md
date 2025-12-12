# PCI Compliance Agent v1.0.0

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
