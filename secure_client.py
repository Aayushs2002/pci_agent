"""
PCI Compliance Agent - Secure Client
Handles secure communication with central server
"""

import json
import ssl
import logging
import requests
from urllib3.exceptions import InsecureRequestWarning
from typing import Dict, Optional
import time
from pathlib import Path

# Disable SSL warnings for development (remove in production)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)

class SecureClient:
    """Handles secure HTTPS communication with central reporting server"""
    
    def __init__(self, config: dict):
        self.config = config
        self.reporting_config = config.get('reporting', {})
        
        # Server configuration
        self.server_url = self.reporting_config.get('server_url')
        self.api_token = self.reporting_config.get('api_token')
        
        # TLS configuration
        self.tls_config = self.reporting_config.get('tls', {})
        self.verify_ssl = self.tls_config.get('verify', True)
        self.client_cert = self.tls_config.get('client_cert')
        self.client_key = self.tls_config.get('client_key')
        self.ca_cert = self.tls_config.get('ca_cert')
        
        # Retry configuration
        self.max_retries = self.reporting_config.get('max_retries', 3)
        self.retry_delay = self.reporting_config.get('retry_delay_seconds', 5)
        
        # Rate limiting
        self.max_requests_per_minute = self.reporting_config.get('max_requests_per_minute', 10)
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_window_start = time.time()
        
        # Initialize session
        self.session = self._create_secure_session()
        
        logger.info(f"SecureClient initialized for {self.server_url}")
    
    def _create_secure_session(self) -> requests.Session:
        """Create a secure requests session with proper TLS configuration"""
        session = requests.Session()
        
        # Set headers
        session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'PCI-Compliance-Agent/1.0',
            'Accept': 'application/json'
        })
        
        # Add API token if configured
        if self.api_token:
            session.headers['Authorization'] = f'Bearer {self.api_token}'
        
        # Configure TLS/SSL
        if self.verify_ssl:
            # Use CA certificate if provided
            if self.ca_cert and Path(self.ca_cert).exists():
                session.verify = self.ca_cert
                logger.info(f"Using CA certificate: {self.ca_cert}")
            else:
                session.verify = True
                logger.info("Using system CA certificates")
        else:
            session.verify = False
            logger.warning("SSL verification disabled - not recommended for production")
        
        # Configure client certificate authentication
        if self.client_cert and self.client_key:
            cert_path = Path(self.client_cert)
            key_path = Path(self.client_key)
            
            if cert_path.exists() and key_path.exists():
                session.cert = (str(cert_path), str(key_path))
                logger.info("Client certificate authentication configured")
            else:
                logger.warning(f"Client certificate files not found: {self.client_cert}, {self.client_key}")
        
        return session
    
    def _check_rate_limit(self):
        """Implement rate limiting to prevent server overload"""
        current_time = time.time()
        
        # Reset counter if window has passed
        if current_time - self.rate_limit_window_start > 60:
            self.request_count = 0
            self.rate_limit_window_start = current_time
        
        # Check if we've exceeded the rate limit
        if self.request_count >= self.max_requests_per_minute:
            sleep_time = 60 - (current_time - self.rate_limit_window_start)
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
                self.request_count = 0
                self.rate_limit_window_start = time.time()
        
        self.request_count += 1
    
    def _make_request(self, method: str, endpoint: str, data: dict = None) -> Optional[dict]:
        """Make HTTP request with retry logic and error handling"""
        if not self.server_url:
            logger.error("No server URL configured")
            return None
        
        url = f"{self.server_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.max_retries + 1):
            try:
                self._check_rate_limit()
                
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                if method.upper() == 'POST':
                    response = self.session.post(url, json=data, timeout=30)
                elif method.upper() == 'GET':
                    response = self.session.get(url, timeout=30)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Check response status
                if response.status_code == 200:
                    logger.debug(f"Request successful: {response.status_code}")
                    return response.json() if response.content else {}
                elif response.status_code == 201:
                    logger.debug(f"Request successful (created): {response.status_code}")
                    return response.json() if response.content else {}
                elif response.status_code in [401, 403]:
                    logger.error(f"Authentication failed: {response.status_code}")
                    return None
                elif response.status_code == 429:
                    logger.warning(f"Server rate limit exceeded: {response.status_code}")
                    time.sleep(self.retry_delay * 2)  # Longer delay for rate limits
                    continue
                else:
                    logger.warning(f"HTTP error {response.status_code}: {response.text}")
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay)
                        continue
                    return None
                    
            except requests.exceptions.SSLError as e:
                logger.error(f"SSL error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries:
                    return None
                time.sleep(self.retry_delay)
                
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries:
                    return None
                time.sleep(self.retry_delay)
                
            except requests.exceptions.Timeout as e:
                logger.warning(f"Request timeout on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries:
                    return None
                time.sleep(self.retry_delay)
                
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries:
                    return None
                time.sleep(self.retry_delay)
        
        return None
    
    def send_report(self, report: dict) -> bool:
        """Send scan report to central server"""
        try:
            logger.info(f"Sending report for scan {report['metadata']['scan_id']}")
            
            # Validate report structure
            if not self._validate_report(report):
                logger.error("Report validation failed")
                return False
            
            # Transform report to server-expected format
            logger.info("About to transform report for server")
            server_report = self._transform_report_for_server(report)
            logger.info("Report transformation completed")
            
            # Debug: Log the transformed report structure
            logger.info(f"Transformed report keys: {list(server_report.keys())}")
            logger.info(f"Agent ID: {server_report.get('agent_id')}, Operator: {server_report.get('operator')}")
            logger.info(f"Scan date: {server_report.get('scan_date')}")
            logger.info(f"Directories: {server_report.get('directories_scanned')}")
            logger.info(f"Total files: {server_report.get('total_files_scanned')}")
            logger.info(f"Findings type: {type(server_report.get('findings'))}")
            logger.info(f"Scan config type: {type(server_report.get('scan_configuration'))}")
            
            # Send report
            response = self._make_request('POST', '/api/reports', server_report)
            
            if response is not None:
                logger.info(f"Report sent successfully: {response.get('report_id', 'unknown')}")
                return True
            else:
                logger.error("Failed to send report")
                return False
                
        except Exception as e:
            logger.error(f"Error sending report: {e}")
            return False
    
    def _transform_report_for_server(self, report: dict) -> dict:
        """Transform internal report format to server-expected format"""
        logger.info(f"Transforming report with keys: {list(report.keys())}")
        metadata = report.get('metadata', {})
        scan_params = report.get('scan_parameters', {})
        scan_results = report.get('scan_results', {})
        summary = scan_results.get('summary', {})
        
        # Convert timestamp to server-expected format
        timestamp = metadata.get('timestamp', '')
        if timestamp and 'T' in timestamp:
            # Convert from ISO format to simple date format if needed
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                scan_date = dt.strftime('%Y-%m-%d')
            except:
                scan_date = timestamp.split('T')[0]  # fallback
        else:
            scan_date = timestamp
        
        # Get directories scanned - need to get actual directories from config
        # For now, we'll need to pass this information through the report
        dirs_count = scan_params.get('directories_scanned', 0)
        # Try to get actual directories if available, otherwise use generic names
        directories_scanned = report.get('actual_directories', [f"directory_{i+1}" for i in range(dirs_count)])
        
        # Transform to server format
        server_report = {
            'agent_id': metadata.get('agent_id', ''),
            'operator': metadata.get('operator', ''),
            'scan_date': scan_date,
            'directories_scanned': directories_scanned,
            'total_files_scanned': summary.get('total_files_scanned', 0),
            'findings': scan_results.get('findings', []),
            'scan_configuration': {
                'exclude_patterns_count': scan_params.get('exclude_patterns_count', 0),
                'detect_plain_pan_enabled': scan_params.get('detect_plain_pan_enabled', False),
                'action_policy': scan_params.get('action_policy', 'report_only'),
                'max_file_size_mb': scan_params.get('max_file_size_mb', 10),
                'concurrency': scan_params.get('concurrency', 4),
                'privacy_settings': scan_params.get('privacy_settings', {})
            },
            'scan_results_summary': {
                'total_files_skipped': summary.get('total_files_skipped', 0),
                'total_directories_scanned': summary.get('total_directories_scanned', 0),
                'total_matches_found': summary.get('total_matches_found', 0),
                'errors_encountered': summary.get('errors_encountered', 0),
                'scan_duration_seconds': summary.get('scan_duration_seconds', 0),
                'findings_by_type': scan_results.get('findings_by_type', {}),
                'risk_assessment': scan_results.get('risk_assessment', {})
            },
            'metadata': {
                'scan_id': metadata.get('scan_id', ''),
                'timestamp': metadata.get('timestamp', ''),
                'report_version': metadata.get('report_version', ''),
                'report_hash': metadata.get('report_hash', '')
            },
            'compliance_notes': report.get('compliance_notes', {})
        }
        
        logger.info(f"Transformed report format for server compatibility")
        logger.info(f"Server report keys: {list(server_report.keys())}")
        logger.info(f"Agent ID: {server_report.get('agent_id')}, Operator: {server_report.get('operator')}")
        return server_report
    
    def register_agent(self, agent_data: dict) -> bool:
        """Register agent with the server"""
        try:
            logger.info("Registering agent with server")
            register_endpoint = self.reporting_config.get('register_endpoint', '/api/agents/register')
            response = self._make_request('POST', register_endpoint, agent_data)
            
            if response is not None:
                logger.info("Agent registered successfully")
                return True
            else:
                logger.error("Agent registration failed")
                return False
                
        except Exception as e:
            logger.error(f"Agent registration error: {e}")
            return False

    def test_connection(self) -> bool:
        """Test connection to server"""
        try:
            logger.info("Testing connection to server")
            response = self._make_request('GET', '/api/health')
            
            if response is not None:
                logger.info("Server connection test successful")
                return True
            else:
                logger.error("Server connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"Connection test error: {e}")
            return False
    
    def get_server_info(self) -> Optional[dict]:
        """Get server information and capabilities"""
        try:
            response = self._make_request('GET', '/api/info')
            return response
        except Exception as e:
            logger.error(f"Error getting server info: {e}")
            return None
    
    def _validate_report(self, report: dict) -> bool:
        """Validate report structure before sending"""
        required_fields = [
            'metadata',
            'scan_parameters',
            'scan_results',
            'compliance_notes'
        ]
        
        for field in required_fields:
            if field not in report:
                logger.error(f"Missing required field in report: {field}")
                return False
        
        # Validate metadata
        metadata = report.get('metadata', {})
        required_metadata = ['agent_id', 'scan_id', 'timestamp', 'operator']
        
        for field in required_metadata:
            if field not in metadata:
                logger.error(f"Missing required metadata field: {field}")
                return False
        
        # Check for sensitive data in report
        if self._contains_sensitive_data(report):
            logger.error("Report contains prohibited sensitive data")
            return False
        
        return True
    
    def _contains_sensitive_data(self, report: dict) -> bool:
        """Check if report contains prohibited sensitive data"""
        # Convert report to string for searching
        report_str = json.dumps(report, default=str).lower()
        
        # Look for patterns that might indicate full PANs
        import re
        
        # Pattern for potential unmasked PANs (not perfect but catches obvious cases)
        pan_pattern = r'\b[0-9]{13,19}\b'
        potential_pans = re.findall(pan_pattern, report_str)
        
        for pan in potential_pans:
            # Skip if it looks like a timestamp or other non-PAN number
            if len(pan) >= 13 and not (pan.startswith('202') or pan.startswith('201')):
                # Basic Luhn check
                digits = [int(d) for d in pan]
                checksum = 0
                parity = len(digits) % 2
                
                for i, digit in enumerate(digits):
                    if i % 2 == parity:
                        digit *= 2
                        if digit > 9:
                            digit -= 9
                    checksum += digit
                
                if checksum % 10 == 0:
                    logger.warning(f"Potential unmasked PAN detected in report: {pan[:4]}****{pan[-4:]}")
                    return True
        
        return False
    
    def close(self):
        """Close the session and cleanup resources"""
        if self.session:
            self.session.close()
            logger.debug("SecureClient session closed")