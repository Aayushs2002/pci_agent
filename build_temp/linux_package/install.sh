#!/bin/bash
# PCI Compliance Agent Installer v1.0.0

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
