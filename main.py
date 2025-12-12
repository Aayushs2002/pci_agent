"""
PCI Compliance Agent - Main Application Entry Point
Coordinates scanning, reporting, and audit logging
"""

import os
import sys
import logging
import yaml
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import uuid

from detection_engine import PANDetector, PANMatch
from file_scanner import FileScanner
from report_generator import ReportGenerator
from secure_client import SecureClient
from audit_logger import AuditLogger
from websocket_client import AgentWebSocketClient

# Ensure logs directory exists
SCRIPT_DIR = Path(__file__).parent.resolve()
LOGS_DIR = SCRIPT_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'pci_agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class PCIComplianceAgent:
    """Main PCI Compliance Agent application"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the PCI Compliance Agent"""
        # Convert config path to absolute if it's relative
        config_path_obj = Path(config_path)
        if not config_path_obj.is_absolute():
            self.config_path = SCRIPT_DIR / config_path
        else:
            self.config_path = config_path_obj
        
        self.config = self._load_config()
        self.agent_id = self._generate_agent_id()
        
        # Initialize components
        self.detector = PANDetector(self.config)
        self.scanner = FileScanner(self.config, self.detector)
        self.report_generator = ReportGenerator(self.config)
        self.secure_client = SecureClient(self.config)
        self.audit_logger = AuditLogger(self.config)
        
        # Initialize WebSocket client for real-time communication
        try:
            self.websocket_client = AgentWebSocketClient(self.config, self.agent_id)
            self.websocket_client.set_scan_command_handler(self._handle_scan_command)
        except Exception as e:
            logger.warning(f"Failed to initialize WebSocket client: {e}")
            self.websocket_client = None
        
        # Scan session info
        self.current_scan_id = None
        self.current_operator = None
        self.current_directories = None  # Store directories for current scan
        self.current_scan_thread = None
        self.scan_running = False
        
        logger.info(f"PCI Compliance Agent initialized (ID: {self.agent_id})")
    
    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                # Try example config if main config doesn't exist
                example_config = config_file.parent / "config.example.yaml"
                if example_config.exists():
                    logger.warning(f"Config file {self.config_path} not found, using example config")
                    config_file = example_config
                else:
                    raise FileNotFoundError(f"No config file found at {self.config_path}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Configuration loaded from {config_file.name}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise  # Re-raise instead of sys.exit to allow caller to handle
    
    def _generate_agent_id(self) -> str:
        """Generate unique agent identifier"""
        # Use machine-specific info for consistent agent ID
        import platform
        machine_info = f"{platform.node()}-{platform.system()}-{platform.machine()}"
        agent_id = hashlib.sha256(machine_info.encode()).hexdigest()[:16]
        return f"pci-agent-{agent_id}"
    
    def _validate_configuration(self) -> bool:
        """Validate critical configuration settings"""
        errors = []
        
        # Check required sections
        required_sections = ['agent', 'reporting', 'privacy', 'detection']
        for section in required_sections:
            if section not in self.config:
                errors.append(f"Missing required configuration section: {section}")
        
        # Validate scan directories
        scan_dirs = self.config.get('agent', {}).get('scan_directories', [])
        if not scan_dirs:
            errors.append("No scan directories configured")
        
        # Check for dangerous settings
        if self.config.get('agent', {}).get('detect_plain_pan', False):
            logger.warning("WARNING: Plain PAN detection is ENABLED - ensure proper authorization!")
        
        if self.config.get('privacy', {}).get('allow_full_pan_retention', False):
            logger.warning("WARNING: Full PAN retention is ENABLED - ensure PCI compliance!")
        
        # Validate server configuration
        server_url = self.config.get('reporting', {}).get('server_url')
        if not server_url or not server_url.startswith('https://'):
            logger.warning("Server URL should use HTTPS for security")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False
        
        return True
    
    def start_scan_session(self, operator: str, directories: List[str] = None) -> str:
        """Start a new scanning session"""
        if not self._validate_configuration():
            raise ValueError("Invalid configuration - cannot start scan")
        
        self.current_scan_id = str(uuid.uuid4())
        self.current_operator = operator
        
        # Use configured directories if none provided
        if not directories:
            directories = self.config.get('agent', {}).get('scan_directories', [])
        
        logger.info(f"Requested scan directories: {directories}")
        
        # Check for whole-system scan marker
        if directories and directories[0] == '*':
            logger.info("Whole system scan requested - discovering all accessible directories")
            valid_directories = self._discover_system_directories()
        else:
            # Validate directories exist and are accessible
            valid_directories = []
            for directory in directories:
                dir_path = os.path.abspath(directory)
                if os.path.exists(dir_path):
                    if os.path.isdir(dir_path):
                        if os.access(dir_path, os.R_OK):
                            valid_directories.append(dir_path)
                            logger.info(f"✓ Directory validated: {dir_path}")
                        else:
                            logger.warning(f"Directory exists but not readable: {dir_path}")
                    else:
                        logger.warning(f"Path exists but is not a directory: {dir_path}")
                else:
                    logger.warning(f"Directory does not exist: {dir_path}")
        
        if not valid_directories:
            error_msg = f"No valid directories to scan. Requested: {directories}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Store the directories for this scan session
        self.current_directories = valid_directories
        
        # Log scan start
        self.audit_logger.log_scan_start(
            scan_id=self.current_scan_id,
            operator=operator,
            directories=valid_directories,
            config_hash=self._get_config_hash()
        )
        
        logger.info(f"Started scan session {self.current_scan_id} by {operator}")
        logger.info(f"Scanning directories: {valid_directories}")
        
        return self.current_scan_id
    
    def _discover_system_directories(self) -> List[str]:
        """Discover all accessible directories on the system for whole-system scan"""
        import platform
        system = platform.system()
        directories = []
        
        try:
            if system == 'Windows':
                # Discover Windows drives and common directories
                import string
                for drive in string.ascii_uppercase:
                    drive_path = f"{drive}:\\"
                    if os.path.exists(drive_path):
                        directories.append(drive_path)
                        logger.info(f"Discovered drive: {drive_path}")
                        
                        # Add common Windows directories
                        for subdir in ['Users', 'ProgramData', 'Program Files', 'inetpub', 'Windows\\Temp']:
                            full_path = os.path.join(drive_path, subdir)
                            if os.path.exists(full_path) and os.access(full_path, os.R_OK):
                                directories.append(full_path)
                                logger.info(f"Discovered directory: {full_path}")
            else:
                # Linux/Unix - discover major directories
                root_dirs = ['/', '/home', '/root', '/var', '/var/www', '/opt', '/tmp', 
                           '/etc', '/usr', '/usr/local', '/srv', '/mnt', '/media']
                for dir_path in root_dirs:
                    if os.path.exists(dir_path) and os.access(dir_path, os.R_OK):
                        directories.append(dir_path)
                        logger.info(f"Discovered directory: {dir_path}")
        except Exception as e:
            logger.error(f"Error discovering system directories: {e}")
            # Fallback to config directories
            directories = self.config.get('agent', {}).get('scan_directories', [])
        
        return directories if directories else [os.getcwd()]
    
    def run_scan(self, progress_callback=None) -> List[PANMatch]:
        """Execute the PAN detection scan"""
        if not self.current_scan_id:
            raise ValueError("No active scan session - call start_scan_session first")
        
        logger.info(f"Starting PAN detection scan (Session: {self.current_scan_id})")
        
        # Use directories from the current scan session, or fall back to config
        directories = self.current_directories or self.config.get('agent', {}).get('scan_directories', [])
        
        try:
            # Reset scanner statistics
            self.scanner.reset_stats()
            
            # Run the scan
            matches = self.scanner.scan_directories(directories, progress_callback)
            
            # Log scan completion
            scan_stats = self.scanner.get_stats()
            self.audit_logger.log_scan_complete(
                scan_id=self.current_scan_id,
                matches_found=len(matches),
                files_scanned=scan_stats['files_scanned'],
                errors=scan_stats['errors']
            )
            
            logger.info(f"Scan completed: {len(matches)} potential PANs found")
            return matches
            
        except Exception as e:
            self.audit_logger.log_scan_error(self.current_scan_id, str(e))
            logger.error(f"Scan failed: {e}")
            raise
    
    def generate_report(self, matches: List[PANMatch]) -> dict:
        """Generate security report from scan results"""
        if not self.current_scan_id:
            raise ValueError("No active scan session")
        
        report = self.report_generator.create_report(
            agent_id=self.agent_id,
            scan_id=self.current_scan_id,
            operator=self.current_operator,
            matches=matches,
            scan_stats=self.scanner.get_stats(),
            config_summary=self._get_config_summary()
        )
        
        # Add actual directories that were scanned for server compatibility
        # Use the directories from the current scan session, not the config
        directories = self.current_directories or self.config.get('agent', {}).get('scan_directories', [])
        report['actual_directories'] = directories
        
        logger.info(f"Generated report with {len(matches)} findings")
        return report
    
    def send_report(self, report: dict) -> bool:
        """Send report to central server securely"""
        try:
            success = self.secure_client.send_report(report)
            
            if success:
                self.audit_logger.log_report_sent(self.current_scan_id, report['metadata']['timestamp'])
                logger.info(f"Report sent successfully for scan {self.current_scan_id}")
            else:
                self.audit_logger.log_report_failed(self.current_scan_id, "Send failed")
                logger.error(f"Failed to send report for scan {self.current_scan_id}")
            
            return success
            
        except Exception as e:
            self.audit_logger.log_report_failed(self.current_scan_id, str(e))
            logger.error(f"Error sending report: {e}")
            return False
    
    def save_report_locally(self, report: dict, file_path: str = None) -> str:
        """Save report to local file"""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            reports_dir = SCRIPT_DIR / 'reports'
            reports_dir.mkdir(exist_ok=True)
            file_path = reports_dir / f"pci_scan_report_{self.current_scan_id}_{timestamp}.json"
        
        # Ensure reports directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Convert Path to string to avoid escape sequence issues
        file_path_str = str(file_path)
        logger.info(f"Report saved to {file_path_str}")
        return file_path_str
    
    def _get_config_hash(self) -> str:
        """Generate hash of current configuration for audit trail"""
        config_str = json.dumps(self.config, sort_keys=True, default=str)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    def _get_config_summary(self) -> dict:
        """Get sanitized configuration summary for reporting"""
        return {
            'scan_directories': len(self.config.get('agent', {}).get('scan_directories', [])),
            'exclude_patterns': len(self.config.get('agent', {}).get('exclude_patterns', [])),
            'detect_plain_pan': self.config.get('agent', {}).get('detect_plain_pan', False),
            'action_policy': self.config.get('agent', {}).get('action_policy', 'report_only'),
            'max_file_size_mb': self.config.get('agent', {}).get('max_file_size_mb', 10),
            'concurrency': self.config.get('agent', {}).get('concurrency', 4),
            'privacy_redact_pan': self.config.get('privacy', {}).get('redact_pan', True),
            'privacy_show_last4_only': self.config.get('privacy', {}).get('show_last4_only', True)
        }
    
    def get_status(self) -> dict:
        """Get current agent status"""
        return {
            'agent_id': self.agent_id,
            'current_scan_id': self.current_scan_id,
            'current_operator': self.current_operator,
            'scan_running': self.scan_running,
            'config_loaded': bool(self.config),
            'components_initialized': True,
            'websocket_connected': self.websocket_client.connected if self.websocket_client else False,
            'last_scan_time': getattr(self, 'last_scan_time', None)
        }
    
    def _handle_scan_command(self, command_data: dict):
        """Handle scan commands from WebSocket"""
        action = command_data.get('action')
        logger.info(f"Received scan command: {action}")
        
        try:
            if action == 'start':
                directories = command_data.get('directories', [])
                operator = command_data.get('operator', 'Remote Operator')
                configuration = command_data.get('configuration', {})
                
                if self.scan_running:
                    logger.warning("Scan already in progress")
                    if self.websocket_client:
                        self.websocket_client.emit_scan_error("Scan already in progress")
                    return
                
                # Start scan in background thread
                import threading
                self.current_scan_thread = threading.Thread(
                    target=self._run_remote_scan,
                    args=(directories, operator, configuration),
                    daemon=True
                )
                self.current_scan_thread.start()
                
            elif action == 'stop':
                if self.scan_running:
                    logger.info("Scan stop requested")
                    self.scan_running = False
                    # Tell scanner to stop gracefully
                    if self.scanner:
                        self.scanner.request_stop()
                    if self.websocket_client:
                        self.websocket_client.emit_scan_completed({
                            'status': 'stopped',
                            'message': 'Scan stopped by user'
                        })
                else:
                    logger.info("No scan running to stop")
                    
            elif action == 'status':
                status = self.get_status()
                if self.websocket_client:
                    self.websocket_client.emit_scan_status(status)
                    
        except Exception as e:
            logger.error(f"Error handling scan command: {e}")
            if self.websocket_client:
                self.websocket_client.emit_scan_error(str(e))
    
    def _run_remote_scan(self, directories: List[str], operator: str, configuration: dict):
        """Run a scan triggered remotely via WebSocket"""
        try:
            self.scan_running = True
            logger.info(f"=== Starting Remote Scan ===")
            logger.info(f"Operator: {operator}")
            logger.info(f"Requested directories: {directories}")
            logger.info(f"Configuration: {configuration}")
            
            # Start scan session with provided directories
            try:
                scan_id = self.start_scan_session(operator, directories)
            except ValueError as e:
                logger.error(f"Failed to start scan session: {e}")
                if self.websocket_client:
                    self.websocket_client.emit_scan_error(str(e))
                return
            
            logger.info(f"Scan session started: {scan_id}")
            logger.info(f"Actual directories to scan: {self.current_directories}")
            
            # Progress callback for WebSocket updates
            def progress_callback(progress):
                if self.websocket_client and self.scan_running:
                    self.websocket_client.emit_scan_progress(progress)
            
            # Run the scan
            logger.info("Starting file scanning...")
            matches = self.run_scan(progress_callback)
            
            if not self.scan_running:
                logger.info("Scan was stopped by user")
                return
            
            # Generate and save report
            logger.info(f"Generating report for {len(matches)} matches...")
            report = self.generate_report(matches)
            logger.info(f"Report generated - Directories scanned: {report.get('actual_directories', [])}")
            
            local_path = self.save_report_locally(report)
            logger.info(f"Report saved locally: {local_path}")
            
            # Send report to server
            logger.info("Sending report to server...")
            success = False
            send_error = None
            try:
                success = self.send_report(report)
                logger.info(f"Report sent to server: {'SUCCESS' if success else 'FAILED'}")
            except Exception as e:
                send_error = str(e)
                logger.error(f"Error sending report: {e}")
            
            # Always notify completion, even if report send failed
            if self.websocket_client:
                completion_data = {
                    'scan_id': scan_id,
                    'matches_found': len(matches),
                    'report_path': local_path,
                    'sent_to_server': success,
                    'status': 'completed',
                    'directories_scanned': self.current_directories
                }
                if send_error:
                    completion_data['send_error'] = send_error
                
                self.websocket_client.emit_scan_completed(completion_data)
                logger.info("Scan completion notification sent to server")
            
            logger.info(f"=== Remote Scan Completed ===")
            logger.info(f"Scan ID: {scan_id}")
            logger.info(f"Matches found: {len(matches)}")
            logger.info(f"Directories scanned: {self.current_directories}")
            logger.info(f"Report saved locally: {local_path}")
            
        except Exception as e:
            logger.error(f"Remote scan failed: {e}", exc_info=True)
            if self.websocket_client:
                self.websocket_client.emit_scan_error(str(e))
        finally:
            self.scan_running = False
    
    def start_websocket_client(self):
        """Start the WebSocket client for remote communication"""
        if self.websocket_client:
            try:
                self.websocket_client.start_background_connection()
                logger.info("WebSocket client started for remote communication")
                return True
            except Exception as e:
                logger.error(f"Failed to start WebSocket client: {e}")
        return False
    
    def register_with_server(self) -> bool:
        """Register this agent with the central server"""
        try:
            import platform
            registration_data = {
                'agent_id': self.agent_id,
                'hostname': platform.node(),
                'version': '1.0.0',
                'os_info': {
                    'system': platform.system(),
                    'release': platform.release(),
                    'version': platform.version(),
                    'machine': platform.machine(),
                    'processor': platform.processor()
                }
            }
            
            success = self.secure_client.register_agent(registration_data)
            if success:
                logger.info("Agent registered with server successfully")
            else:
                logger.warning("Failed to register agent with server")
            return success
            
        except Exception as e:
            logger.error(f"Agent registration failed: {e}")
            return False

def create_cli_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(description="PCI Compliance Agent")
    parser.add_argument('--config', '-c', default='config.yaml',
                       help='Configuration file path')
    parser.add_argument('--operator', '-o', required=False,
                       help='Operator name for audit logging (required for CLI scans, optional for WebSocket mode)')
    parser.add_argument('--directories', '-d', nargs='+',
                       help='Directories to scan (overrides config)')
    parser.add_argument('--output', '-O', 
                       help='Output file for report (optional)')
    parser.add_argument('--no-send', action='store_true',
                       help='Skip sending report to server')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--websocket-mode', action='store_true',
                       help='Run in WebSocket mode for remote control')
    parser.add_argument('--server-url',
                       help='Server URL for WebSocket connection (overrides config)')
    parser.add_argument('--output-format', choices=['json', 'csv'], default='json',
                       help='Output format for reports')
    return parser

def main():
    """Main CLI entry point"""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Ensure required directories exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    try:
        # Initialize agent
        agent = PCIComplianceAgent(args.config)
        
        # Check if websocket mode should be enabled by default from config
        websocket_mode = args.websocket_mode or agent.config.get('reporting', {}).get('websocket_mode', False)
        
        # Handle WebSocket mode
        if websocket_mode:
            logger.info("Starting agent in WebSocket mode for remote control")
            
            # Override server URLs if provided via command line
            if args.server_url:
                logger.info(f"Using command-line server URL: {args.server_url}")
                agent.config['reporting']['server_url'] = args.server_url
                agent.config['reporting']['websocket_url'] = args.server_url
                # Reinitialize secure client with new URL
                agent.secure_client = SecureClient(agent.config)
                # Reinitialize WebSocket client with new URL
                from websocket_client import AgentWebSocketClient
                agent.websocket_client = AgentWebSocketClient(agent.config, agent.agent_id)
                agent.websocket_client.set_scan_command_handler(agent._handle_scan_command)
            
            # Register with server
            agent.register_with_server()
            
            # Start WebSocket client
            agent.start_websocket_client()
            
            logger.info("Agent ready for remote commands. Press Ctrl+C to exit.")
            
            # Keep the agent running and listening for commands
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("WebSocket mode interrupted by user")
                if agent.websocket_client:
                    agent.websocket_client.disconnect()
                sys.exit(0)
            
            return
        
        # Regular CLI mode
        if not args.operator:
            logger.error("Operator name is required for CLI mode")
            sys.exit(1)
        
        # Start scan session
        scan_id = agent.start_scan_session(args.operator, args.directories)
        
        # Run scan with progress updates
        def progress_callback(progress):
            print(f"Progress: {progress['files_completed']}/{progress['total_files']} files, "
                  f"{progress['matches_found']} matches found")
        
        matches = agent.run_scan(progress_callback)
        
        # Generate report
        report = agent.generate_report(matches)
        
        # Save report locally
        local_path = agent.save_report_locally(report, args.output)
        print(f"Report saved to: {local_path}")
        
        # Send report to server (unless disabled)
        if not args.no_send:
            if agent.send_report(report):
                print("Report sent to server successfully")
            else:
                print("Failed to send report to server")
        
        # Print summary
        print(f"\nScan Summary:")
        print(f"Scan ID: {scan_id}")
        print(f"Files scanned: {agent.scanner.get_stats()['files_scanned']}")
        print(f"Potential PANs found: {len(matches)}")
        print(f"Errors: {agent.scanner.get_stats()['errors']}")
        
        # Exit with appropriate code
        sys.exit(0 if len(matches) == 0 else 1)
        
    except KeyboardInterrupt:
        logger.info("Scan interrupted by user")
        sys.exit(130)
    except Exception as e:
        import traceback
        logger.error(f"Agent execution failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()