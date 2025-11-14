"""
PCI Compliance Agent - Audit Logger
Comprehensive audit logging for compliance and security
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib
import threading

logger = logging.getLogger(__name__)

class AuditLogger:
    """Handles comprehensive audit logging for PCI compliance"""
    
    def __init__(self, config: dict):
        self.config = config
        self.privacy_config = config.get('privacy', {})
        self.audit_config = config.get('audit', {})
        
        # Get script directory for absolute paths
        script_dir = Path(__file__).parent.resolve()
        
        # Audit log configuration - check both privacy and audit sections
        audit_log_rel = self.privacy_config.get('audit_log') or self.audit_config.get('log_file', 'logs/audit.log')
        
        # Convert to absolute path if relative
        audit_log_path = Path(audit_log_rel)
        if not audit_log_path.is_absolute():
            audit_log_path = script_dir / audit_log_path
        
        self.audit_log_path = str(audit_log_path)
        self.enable_detailed_logging = self.privacy_config.get('enable_detailed_logging', True)
        
        # Ensure log directory exists
        log_dir = Path(self.audit_log_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Initialize audit log file
        self._initialize_audit_log()
        
        logger.info(f"AuditLogger initialized: {self.audit_log_path}")
    
    def _initialize_audit_log(self):
        """Initialize audit log file with header information"""
        try:
            # Check if log file exists and is recent
            log_path = Path(self.audit_log_path)
            
            if not log_path.exists():
                self._write_audit_entry({
                    "event_type": "audit_log_initialized",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message": "PCI Compliance Agent audit logging started",
                    "version": "1.0"
                })
                logger.info("Audit log initialized")
        
        except Exception as e:
            logger.error(f"Failed to initialize audit log: {e}")
    
    def _write_audit_entry(self, entry: dict):
        """Write audit entry to log file with thread safety"""
        try:
            with self._lock:
                with open(self.audit_log_path, 'a', encoding='utf-8') as f:
                    json.dump(entry, f, default=str)
                    f.write('\n')
        except Exception as e:
            logger.error(f"Failed to write audit entry: {e}")
    
    def _create_base_entry(self, event_type: str, **kwargs) -> dict:
        """Create base audit entry with common fields"""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "process_id": os.getpid(),
            "thread_id": threading.get_ident()
        }
        entry.update(kwargs)
        return entry
    
    def log_scan_start(self, scan_id: str, operator: str, directories: List[str], 
                      config_hash: str):
        """Log the start of a scan session"""
        entry = self._create_base_entry(
            "scan_started",
            scan_id=scan_id,
            operator=operator,
            directories_count=len(directories),
            directories=directories if self.enable_detailed_logging else ["<redacted>"],
            config_hash=config_hash
        )
        
        self._write_audit_entry(entry)
        logger.info(f"Audit: Scan started by {operator} (ID: {scan_id})")
    
    def log_scan_complete(self, scan_id: str, matches_found: int, 
                         files_scanned: int, errors: int):
        """Log successful completion of a scan"""
        entry = self._create_base_entry(
            "scan_completed",
            scan_id=scan_id,
            matches_found=matches_found,
            files_scanned=files_scanned,
            errors=errors,
            status="success"
        )
        
        self._write_audit_entry(entry)
        logger.info(f"Audit: Scan completed (ID: {scan_id}) - {matches_found} matches found")
    
    def log_scan_error(self, scan_id: str, error_message: str):
        """Log scan failure or error"""
        entry = self._create_base_entry(
            "scan_error",
            scan_id=scan_id,
            error_message=error_message,
            status="error"
        )
        
        self._write_audit_entry(entry)
        logger.error(f"Audit: Scan error (ID: {scan_id}) - {error_message}")
    
    def log_pan_detection(self, scan_id: str, file_path: str, line_number: int, 
                         card_type: str, luhn_valid: bool, confidence: float, 
                         is_masked: bool, action_taken: str = "reported"):
        """Log PAN detection event with privacy controls"""
        # Sanitize file path for logging
        sanitized_path = self._sanitize_file_path(file_path)
        
        entry = self._create_base_entry(
            "pan_detected",
            scan_id=scan_id,
            file_path=sanitized_path,
            line_number=line_number,
            card_type=card_type,
            luhn_valid=luhn_valid,
            confidence_score=confidence,
            is_masked=is_masked,
            action_taken=action_taken,
            risk_level=self._assess_finding_risk(luhn_valid, is_masked, confidence)
        )
        
        self._write_audit_entry(entry)
        
        if luhn_valid and not is_masked:
            logger.warning(f"Audit: HIGH RISK PAN detected in {sanitized_path}:{line_number}")
        else:
            logger.info(f"Audit: PAN candidate detected in {sanitized_path}:{line_number}")
    
    def log_report_generated(self, scan_id: str, report_hash: str, 
                           findings_count: int):
        """Log report generation"""
        entry = self._create_base_entry(
            "report_generated",
            scan_id=scan_id,
            report_hash=report_hash,
            findings_count=findings_count
        )
        
        self._write_audit_entry(entry)
        logger.info(f"Audit: Report generated for scan {scan_id} with {findings_count} findings")
    
    def log_report_sent(self, scan_id: str, timestamp: str, server_response: str = None):
        """Log successful report transmission"""
        entry = self._create_base_entry(
            "report_sent",
            scan_id=scan_id,
            sent_timestamp=timestamp,
            server_response=server_response,
            status="success"
        )
        
        self._write_audit_entry(entry)
        logger.info(f"Audit: Report sent successfully for scan {scan_id}")
    
    def log_report_failed(self, scan_id: str, error_message: str):
        """Log failed report transmission"""
        entry = self._create_base_entry(
            "report_send_failed",
            scan_id=scan_id,
            error_message=error_message,
            status="failed"
        )
        
        self._write_audit_entry(entry)
        logger.error(f"Audit: Report send failed for scan {scan_id} - {error_message}")
    
    def log_config_change(self, operator: str, setting: str, old_value: Any, 
                         new_value: Any, justification: str = None):
        """Log configuration changes"""
        # Sanitize sensitive values
        if 'password' in setting.lower() or 'token' in setting.lower() or 'key' in setting.lower():
            old_value = "<redacted>" if old_value else None
            new_value = "<redacted>" if new_value else None
        
        entry = self._create_base_entry(
            "config_changed",
            operator=operator,
            setting=setting,
            old_value=old_value,
            new_value=new_value,
            justification=justification
        )
        
        self._write_audit_entry(entry)
        logger.info(f"Audit: Configuration changed by {operator}: {setting}")
    
    def log_user_action(self, operator: str, action: str, details: dict = None):
        """Log user actions for accountability"""
        entry = self._create_base_entry(
            "user_action",
            operator=operator,
            action=action,
            details=details or {}
        )
        
        self._write_audit_entry(entry)
        logger.info(f"Audit: User action by {operator}: {action}")
    
    def log_security_event(self, event_type: str, severity: str, message: str, 
                          details: dict = None):
        """Log security-related events"""
        entry = self._create_base_entry(
            "security_event",
            security_event_type=event_type,
            severity=severity,
            message=message,
            details=details or {}
        )
        
        self._write_audit_entry(entry)
        
        if severity.lower() in ['high', 'critical']:
            logger.warning(f"Audit: SECURITY EVENT [{severity}] {event_type}: {message}")
        else:
            logger.info(f"Audit: Security event [{severity}] {event_type}: {message}")
    
    def log_file_access(self, scan_id: str, file_path: str, access_type: str, 
                       status: str, error_message: str = None):
        """Log file access attempts"""
        if not self.enable_detailed_logging:
            return  # Skip detailed file access logging if disabled
        
        sanitized_path = self._sanitize_file_path(file_path)
        
        entry = self._create_base_entry(
            "file_access",
            scan_id=scan_id,
            file_path=sanitized_path,
            access_type=access_type,  # read, scan, etc.
            status=status,  # success, failed, skipped
            error_message=error_message
        )
        
        self._write_audit_entry(entry)
        
        if status == "failed" and error_message:
            logger.debug(f"Audit: File access failed - {sanitized_path}: {error_message}")
    
    def _sanitize_file_path(self, file_path: str) -> str:
        """Sanitize file paths to remove sensitive information"""
        import re
        # Remove usernames from paths
        sanitized = re.sub(r'/Users/[^/]+/', '/Users/<user>/', file_path)
        sanitized = re.sub(r'\\Users\\[^\\]+\\', '\\Users\\<user>\\', sanitized)
        sanitized = re.sub(r'C:\\Users\\[^\\]+\\', 'C:\\Users\\<user>\\', sanitized)
        return sanitized
    
    def _assess_finding_risk(self, luhn_valid: bool, is_masked: bool, 
                           confidence: float) -> str:
        """Assess risk level of a finding for audit purposes"""
        if luhn_valid and not is_masked and confidence > 0.8:
            return "critical"
        elif luhn_valid and not is_masked:
            return "high"
        elif luhn_valid and is_masked:
            return "medium"
        else:
            return "low"
    
    def generate_audit_summary(self, start_time: datetime = None, 
                             end_time: datetime = None) -> dict:
        """Generate summary of audit events for a time period"""
        try:
            summary = {
                "scans_started": 0,
                "scans_completed": 0,
                "scans_failed": 0,
                "total_findings": 0,
                "high_risk_findings": 0,
                "reports_sent": 0,
                "reports_failed": 0,
                "config_changes": 0,
                "security_events": 0
            }
            
            with open(self.audit_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Filter by time if specified
                        if start_time or end_time:
                            entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                            if start_time and entry_time < start_time:
                                continue
                            if end_time and entry_time > end_time:
                                continue
                        
                        # Count events
                        event_type = entry.get('event_type', '')
                        
                        if event_type == 'scan_started':
                            summary['scans_started'] += 1
                        elif event_type == 'scan_completed':
                            summary['scans_completed'] += 1
                            summary['total_findings'] += entry.get('matches_found', 0)
                        elif event_type == 'scan_error':
                            summary['scans_failed'] += 1
                        elif event_type == 'pan_detected' and entry.get('risk_level') in ['high', 'critical']:
                            summary['high_risk_findings'] += 1
                        elif event_type == 'report_sent':
                            summary['reports_sent'] += 1
                        elif event_type == 'report_send_failed':
                            summary['reports_failed'] += 1
                        elif event_type == 'config_changed':
                            summary['config_changes'] += 1
                        elif event_type == 'security_event':
                            summary['security_events'] += 1
                            
                    except json.JSONDecodeError:
                        continue
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate audit summary: {e}")
            return {}
    
    def export_audit_log(self, output_path: str, start_time: datetime = None, 
                        end_time: datetime = None, event_types: List[str] = None):
        """Export filtered audit log to a new file"""
        try:
            exported_count = 0
            
            with open(self.audit_log_path, 'r', encoding='utf-8') as infile:
                with open(output_path, 'w', encoding='utf-8') as outfile:
                    for line in infile:
                        try:
                            entry = json.loads(line.strip())
                            
                            # Apply filters
                            if start_time or end_time:
                                entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                                if start_time and entry_time < start_time:
                                    continue
                                if end_time and entry_time > end_time:
                                    continue
                            
                            if event_types and entry.get('event_type') not in event_types:
                                continue
                            
                            outfile.write(line)
                            exported_count += 1
                            
                        except json.JSONDecodeError:
                            continue
            
            logger.info(f"Exported {exported_count} audit entries to {output_path}")
            return exported_count
            
        except Exception as e:
            logger.error(f"Failed to export audit log: {e}")
            return 0