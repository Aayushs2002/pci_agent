# Building PCI Compliance Agent for Linux

This guide explains how to build the PCI Compliance Agent on a Linux system.

## Prerequisites

### System Requirements
- Linux distribution (Ubuntu 20.04+, CentOS 8+, Debian 10+, or similar)
- Python 3.8 or higher
- pip (Python package manager)
- git (optional, for cloning)

### Install Dependencies

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv build-essential
```

#### CentOS/RHEL:
```bash
sudo yum install -y python3 python3-pip python3-devel gcc
```

#### Arch Linux:
```bash
sudo pacman -S python python-pip base-devel
```

## Build Process

### 1. Transfer Files to Linux System

Copy the entire `pci-compliance-agent` folder to your Linux machine:

```bash
# Using scp from Windows to Linux
scp -r e:\personalProject\pci-compliane\pci-compliance-agent user@linux-server:/home/user/

# Or use git to clone on Linux
git clone <your-repo> /home/user/pci-compliance-agent
```

### 2. Install Python Dependencies

```bash
cd /home/user/pci-compliance-agent

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install runtime dependencies
pip install -r requirements.txt

# Install build dependencies
pip install pyinstaller>=5.13.0 setuptools>=68.0.0
```

### 3. Build the Agent

```bash
python3 build_agent.py
```

This will create:
- `dist/pci-agent` - The standalone executable
- `installers/pci-compliance-agent-1.0.0-linux-x64.tar.gz` - Installation package

### 4. Verify the Build

```bash
# Check if executable was created
ls -lh dist/pci-agent

# Test the executable
dist/pci-agent --version

# Check installer
ls -lh installers/*.tar.gz
```

## Installation on Linux

### Extract the Package

```bash
cd installers
tar -xzf pci-compliance-agent-1.0.0-linux-x64.tar.gz
cd pci-compliance-agent-1.0.0
```

### Run Installation Script

```bash
sudo ./install.sh
```

This will:
- Copy `pci-agent` to `/usr/local/bin/`
- Create config directory: `/etc/pci-compliance-agent/`
- Create log directory: `/var/log/pci-compliance-agent/`
- Create reports directory: `/var/lib/pci-compliance-agent/reports/`
- Install systemd service (optional)

## Configuration

Edit the configuration file:

```bash
sudo nano /etc/pci-compliance-agent/config.yaml
```

Key settings to configure:

```yaml
server:
  url: "http://your-server:3001"  # Your PCI compliance server
  websocket_url: "http://your-server:3001"

agent:
  id: "agent-linux-001"
  name: "Linux Server Scanner"
  
scan:
  directories:
    - /home
    - /var/www
    - /opt
  exclude_dirs:
    - /proc
    - /sys
    - /dev
    
performance:
  concurrency: 16           # Number of scanning threads
  batch_size: 5000         # Files per batch
  fast_mode: true          # Enable streaming mode (faster)
  progress_update_interval: 100  # Update every N files
```

## Running the Agent

### Manual Mode (WebSocket)

```bash
pci-agent --websocket-mode --server-url http://your-server:3001
```

### CLI Mode (Direct Scan)

```bash
pci-agent --operator "Admin Name" --directories /home/users /var/www
```

### As a Systemd Service

Enable and start the service:

```bash
# Edit the service file to set your server URL
sudo nano /etc/systemd/system/pci-agent.service

# Modify the ExecStart line:
# ExecStart=/usr/local/bin/pci-agent --websocket-mode --server-url http://your-server:3001

# Enable service to start on boot
sudo systemctl enable pci-agent

# Start the service
sudo systemctl start pci-agent

# Check status
sudo systemctl status pci-agent

# View logs
sudo journalctl -u pci-agent -f
```

## Troubleshooting

### Build Errors

#### Missing Python.h
```bash
# Ubuntu/Debian
sudo apt-get install python3-dev

# CentOS/RHEL
sudo yum install python3-devel
```

#### PyInstaller Errors
```bash
# Reinstall PyInstaller
pip uninstall pyinstaller
pip install pyinstaller==5.13.0
```

### Permission Errors

```bash
# Make sure the executable has correct permissions
sudo chmod +x /usr/local/bin/pci-agent

# Check log directory permissions
sudo chmod 755 /var/log/pci-compliance-agent
```

### Connection Issues

```bash
# Test server connectivity
curl http://your-server:3001/health

# Check firewall
sudo ufw status
sudo ufw allow 3001/tcp

# Test WebSocket connection
telnet your-server 3001
```

### Performance Tuning

For large file systems, optimize the configuration:

```yaml
performance:
  concurrency: 32          # Increase for faster servers
  batch_size: 10000       # Larger batches for HDD systems
  fast_mode: true         # Always use streaming mode
  progress_update_interval: 200  # Less frequent updates
```

## Transferring Build to Windows Server

After building on Linux, transfer the installer back:

```bash
# From Linux to Windows
scp installers/pci-compliance-agent-1.0.0-linux-x64.tar.gz user@windows-server:E:\builds\

# Or upload to your file server for GUI downloads
```

## Security Considerations

### File Permissions

```bash
# Secure the config file
sudo chmod 600 /etc/pci-compliance-agent/config.yaml
sudo chown root:root /etc/pci-compliance-agent/config.yaml
```

### Running as Non-Root (Recommended)

Create a dedicated user:

```bash
sudo useradd -r -s /bin/false pci-agent
sudo chown -R pci-agent:pci-agent /var/log/pci-compliance-agent
sudo chown -R pci-agent:pci-agent /var/lib/pci-compliance-agent

# Edit systemd service
sudo nano /etc/systemd/system/pci-agent.service

# Change User line:
# User=pci-agent
# Group=pci-agent

sudo systemctl daemon-reload
sudo systemctl restart pci-agent
```

### SELinux (CentOS/RHEL)

If SELinux is enabled:

```bash
# Allow network connections
sudo setsebool -P httpd_can_network_connect 1

# Or create custom policy if needed
```

## Automated Build Script

For automated builds, create a build script:

```bash
#!/bin/bash
# build_linux_agent.sh

set -e

echo "Building PCI Compliance Agent for Linux..."

# Install dependencies
pip3 install -r requirements.txt
pip3 install pyinstaller>=5.13.0 setuptools>=68.0.0

# Build
python3 build_agent.py

# Verify
if [ -f "installers/pci-compliance-agent-1.0.0-linux-x64.tar.gz" ]; then
    echo "✅ Build successful!"
    ls -lh installers/*.tar.gz
    exit 0
else
    echo "❌ Build failed!"
    exit 1
fi
```

Make it executable:

```bash
chmod +x build_linux_agent.sh
./build_linux_agent.sh
```

## Docker Build (Alternative)

Build in a Docker container for consistency:

```bash
# Create Dockerfile
cat > Dockerfile.build << 'EOF'
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY . .

RUN pip3 install -r requirements.txt && \
    pip3 install pyinstaller>=5.13.0 setuptools>=68.0.0

CMD ["python3", "build_agent.py"]
EOF

# Build image
docker build -f Dockerfile.build -t pci-agent-builder .

# Run build
docker run --rm -v $(pwd)/installers:/build/installers pci-agent-builder

# Extract installer
ls -lh installers/*.tar.gz
```

## Support

For issues or questions:
- Check logs: `/var/log/pci-compliance-agent/`
- GitHub Issues: [your-repo-url]
- Documentation: [your-docs-url]
