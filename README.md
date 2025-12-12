# PCI Compliance Agent

A standalone Python application for scanning files and directories to detect potential Payment Card Numbers (PANs) in compliance with PCI-DSS requirements.

## Features

- **Advanced PAN Detection**: Uses regex patterns and Luhn algorithm validation
- **Multi-Card Support**: Detects Visa, Mastercard, AMEX, Discover, Diners, and JCB cards
- **Security-First Design**: Data minimization, masking, and secure handling
- **Configurable Scanning**: Flexible directory and file type filtering
- **Audit Logging**: Comprehensive audit trails for compliance
- **Secure Reporting**: Encrypted transmission to central server
- **Cross-Platform**: Runs on Windows, Linux, and macOS
- **🚀 Performance Optimized**: 5-10x faster scanning with streaming mode
- **☁️ Remote Management**: WebSocket-based control from central GUI
- **📦 Multi-Platform Builds**: Windows and Linux installers

## Platform Support

### Windows
- ✅ Standalone `.exe` installer
- ✅ Windows Service support
- ✅ GUI launcher included

### Linux
- ✅ Standalone binary in `.tar.gz`
- ✅ Systemd service support
- ✅ Ubuntu, CentOS, Debian compatible

📖 **See [MULTI_PLATFORM_DEPLOYMENT.md](../MULTI_PLATFORM_DEPLOYMENT.md)** for cross-platform build and deployment guide.

📖 **See [BUILD_LINUX.md](BUILD_LINUX.md)** for detailed Linux build instructions.

## Quick Start

### Option 1: Download Pre-Built Installer (Recommended)

1. Access the PCI Compliance GUI at `http://your-server:3001`
2. Navigate to **Deployment** tab
3. Download installer for your platform:
   - Windows: `pci-compliance-agent-1.0.0-windows-x64.zip`
   - Linux: `pci-compliance-agent-1.0.0-linux-x64.tar.gz`
4. Follow installation instructions shown in GUI

### Option 2: Build from Source

#### Windows
```powershell
cd pci-compliance-agent
python build_agent.py
```

#### Linux
```bash
cd pci-compliance-agent
python3 build_agent.py
```

See build documentation for detailed instructions.

## Prerequisites

### For Running Agent
- Python 3.8+ (if running from source)
- Network access to PCI Compliance Server (WebSocket mode)

### For Building Agent
- Python 3.8 or higher
- pip package manager
- PyInstaller 5.13.0+
- Build tools (gcc on Linux, Visual Studio on Windows)

## Installation

1. Clone or download this repository:
```bash
git clone <repository-url>
cd pci-compliance-agent
```

2. Create a virtual environment:
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS  
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create configuration file:
```bash
cp config.example.yaml config.yaml
```

5. Edit `config.yaml` with your settings

## Configuration

### Basic Configuration

Edit `config.yaml` to configure:

```yaml
agent:
  scan_directories:
    - "C:\\temp"
    - "C:\\Users\\Public\\Documents"
  exclude_patterns:
    - "*.exe"
    - "*.dll"
  max_file_size_mb: 10

detection:
  require_luhn_validation: true
  minimum_confidence_score: 0.7

reporting:
  server_url: "https://your-server.com:8443"
  api_token: "your-api-token"
```

### Security Settings

**IMPORTANT**: Review these security-critical settings:

- `detect_plain_pan`: Only enable with proper authorization
- `allow_full_pan_retention`: Keep disabled for PCI compliance
- `redact_pan`: Keep enabled to protect sensitive data

## Usage

### Basic Scanning

```bash
python main.py --operator "john.doe" --directories "C:\temp" "D:\data"
```

### Advanced Options

```bash
# Scan with custom config
python main.py --config custom.yaml --operator "jane.smith"

# Scan without sending to server
python main.py --operator "admin" --no-send

# Verbose output
python main.py --operator "admin" --verbose

# Save report to specific file
python main.py --operator "admin" --output "report.json"
```

### Command Line Options

- `--operator, -o`: Operator name (required for audit logging)
- `--config, -c`: Configuration file path (default: config.yaml)
- `--directories, -d`: Directories to scan (overrides config)
- `--output, -O`: Output file for report
- `--no-send`: Skip sending report to server
- `--verbose, -v`: Enable verbose logging
- `--output-format`: Output format (json, csv)

## Security Considerations

### Data Protection

- **Never store unmasked PANs**: Configure `allow_full_pan_retention: false`
- **Use data masking**: Enable `redact_pan: true`
- **Secure transmission**: Use HTTPS with valid certificates
- **Access controls**: Restrict who can run scans

### PCI-DSS Compliance

- Only scan authorized systems
- Ensure proper data handling procedures
- Maintain audit logs for compliance
- Follow data retention policies
- Use secure communication channels

### Authorization

**WARNING**: This tool can detect sensitive payment card data. Ensure you have proper authorization before scanning:

- Written approval from data owners
- Compliance with organizational policies
- PCI-DSS authorization if applicable
- Legal review for regulatory compliance

## Output

### Scan Results

The agent produces structured reports containing:

```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-10-13T14:30:00Z",
  "operator": "john.doe",
  "agent_id": "pci-agent-abc123",
  "summary": {
    "files_scanned": 1250,
    "potential_pans_found": 3,
    "scan_duration": "0:02:45"
  },
  "findings": [
    {
      "file_path": "/path/to/file.txt",
      "line_number": 42,
      "card_type": "visa",
      "masked_pan": "****1234",
      "confidence_score": 0.95,
      "luhn_valid": true
    }
  ]
}
```

### Exit Codes

- `0`: No PANs found (clean scan)
- `1`: PANs found (findings detected)  
- `130`: Interrupted by user (Ctrl+C)
- Other: Error occurred

## Logging

### Application Logs
- Location: `logs/pci_agent.log`
- Contains scan progress and system events
- Sensitive data is masked

### Audit Logs  
- Location: `logs/audit.log`
- Compliance-focused logging
- 365-day retention by default
- Tamper-evident format

## Integration

### Server Integration

Configure the agent to send reports to a central server:

```yaml
reporting:
  server_url: "https://pci-server.company.com:8443"
  api_endpoint: "/api/reports"
  api_token: "${PCI_API_TOKEN}"
  verify_ssl: true
```

### Environment Variables

Set sensitive values via environment variables:

```bash
export PCI_API_TOKEN="your-secure-token"
export PCI_SERVER_URL="https://your-server.com:8443"
```

### Automation

Run automated scans with cron/Task Scheduler:

```bash
# Daily scan at 2 AM
0 2 * * * /path/to/venv/bin/python /path/to/main.py --operator "automated"
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Adding Detection Rules

Extend `detection_engine.py` to add new card types or patterns:

```python
CARD_PATTERNS = {
    CardType.CUSTOM: r'custom_pattern_here',
    # ... existing patterns
}
```

### Custom Reporting

Extend `report_generator.py` for custom report formats:

```python
def generate_custom_report(self, matches, format_type):
    # Custom report logic
    pass
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Run with appropriate permissions
   - Check directory access rights
   - Verify file ownership

2. **Config File Not Found**
   - Ensure `config.yaml` exists
   - Use `--config` to specify path
   - Check file permissions

3. **Network Connection Failed**
   - Verify server URL and port
   - Check firewall settings
   - Validate SSL certificates
   - Test with `--no-send` flag

4. **High Memory Usage**
   - Reduce `max_file_size_mb`
   - Lower `concurrency` setting
   - Exclude large binary files

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
python main.py --operator "debug" --verbose
```

### Log Analysis

Check logs for detailed information:

```bash
# View recent application logs
tail -f logs/pci_agent.log

# Search audit logs
grep "SCAN_START" logs/audit.log
```

## Architecture

### Components

- **detection_engine.py**: Core PAN detection with Luhn validation
- **file_scanner.py**: File system traversal and scanning
- **report_generator.py**: Report creation and formatting
- **secure_client.py**: Secure server communication
- **audit_logger.py**: Compliance audit logging
- **main.py**: CLI interface and orchestration

### Data Flow

```
Directories → File Scanner → Detection Engine → Report Generator → Secure Client → Server
                    ↓
                Audit Logger
```

## Support

For issues and support:

1. Check the logs in `logs/` directory
2. Verify configuration settings
3. Test with minimal scan scope
4. Review security and permissions
5. Consult PCI-DSS guidance

## Compliance Notes

This tool is designed to support PCI-DSS compliance efforts but does not guarantee compliance. Organizations must:

- Implement proper data governance
- Follow secure coding practices  
- Maintain audit trails
- Regularly review and update procedures
- Ensure proper staff training

## License

MIT License - See LICENSE file for details