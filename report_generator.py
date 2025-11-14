"""
PCI Compliance Agent - Report Generator
Creates secure, compliant reports from scan results
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Optional
import logging

from detection_engine import PANMatch, CardType

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates PCI-compliant scan reports with security considerations"""
    
    def __init__(self, config: dict):
        self.config = config
        self.privacy_config = config.get('privacy', {})
        
        # Privacy settings
        self.allow_full_pan = self.privacy_config.get('allow_full_pan_retention', False)
        self.redact_pan = self.privacy_config.get('redact_pan', True)
        self.show_last4_only = self.privacy_config.get('show_last4_only', True)
        self.hash_sensitive_data = self.privacy_config.get('hash_sensitive_data', True)
        
        logger.info(f"ReportGenerator initialized: full_pan_allowed={self.allow_full_pan}, "
                   f"redact_pan={self.redact_pan}")
    
    def create_report(self, agent_id: str, scan_id: str, operator: str, 
                     matches: List[PANMatch], scan_stats: dict, 
                     config_summary: dict) -> dict:
        """
        Create comprehensive scan report following PCI compliance guidelines
        """
        timestamp = datetime.now(timezone.utc)
        
        report = {
            "metadata": {
                "report_version": "1.0",
                "agent_id": agent_id,
                "scan_id": scan_id,
                "timestamp": timestamp.isoformat(),
                "operator": operator,
                "report_hash": "",  # Will be calculated after report creation
            },
            
            "scan_parameters": {
                "directories_scanned": config_summary.get('scan_directories', 0),
                "exclude_patterns_count": config_summary.get('exclude_patterns', 0),
                "detect_plain_pan_enabled": config_summary.get('detect_plain_pan', False),
                "action_policy": config_summary.get('action_policy', 'report_only'),
                "max_file_size_mb": config_summary.get('max_file_size_mb', 10),
                "concurrency": config_summary.get('concurrency', 4),
                "privacy_settings": {
                    "redact_pan": config_summary.get('privacy_redact_pan', True),
                    "show_last4_only": config_summary.get('privacy_show_last4_only', True)
                }
            },
            
            "scan_results": {
                "summary": {
                    "total_files_scanned": scan_stats.get('files_scanned', 0),
                    "total_files_skipped": scan_stats.get('files_skipped', 0),
                    "total_directories_scanned": scan_stats.get('directories_scanned', 0),
                    "total_matches_found": len(matches),
                    "errors_encountered": scan_stats.get('errors', 0),
                    "scan_duration_seconds": scan_stats.get('duration_seconds', 0)
                },
                
                "findings_by_type": self._categorize_findings(matches),
                
                "findings": self._process_findings(matches),
                
                "risk_assessment": self._assess_risk(matches)
            },
            
            "compliance_notes": {
                "data_handling": "This report follows PCI-DSS data minimization principles",
                "retention_policy": "Sensitive data is masked unless explicitly authorized",
                "audit_trail": f"Full audit log available for scan {scan_id}",
                "recommendations": self._generate_recommendations(matches)
            }
        }
        
        # Calculate report hash for integrity
        report_json = json.dumps(report, sort_keys=True, default=str)
        report["metadata"]["report_hash"] = hashlib.sha256(report_json.encode()).hexdigest()
        
        logger.info(f"Generated report for scan {scan_id}: {len(matches)} findings")
        return report
    
    def _categorize_findings(self, matches: List[PANMatch]) -> dict:
        """Categorize findings by card type, validation status, etc."""
        categories = {
            "by_card_type": {},
            "by_validation_status": {
                "luhn_valid": 0,
                "luhn_invalid": 0
            },
            "by_confidence": {
                "high": 0,    # > 0.8
                "medium": 0,  # 0.5 - 0.8
                "low": 0      # < 0.5
            },
            "by_masking_status": {
                "masked": 0,
                "unmasked": 0
            }
        }
        
        for match in matches:
            # Card type categorization
            card_type = match.card_type.value
            categories["by_card_type"][card_type] = categories["by_card_type"].get(card_type, 0) + 1
            
            # Validation status
            if match.luhn_valid:
                categories["by_validation_status"]["luhn_valid"] += 1
            else:
                categories["by_validation_status"]["luhn_invalid"] += 1
            
            # Confidence level
            if match.confidence_score > 0.8:
                categories["by_confidence"]["high"] += 1
            elif match.confidence_score > 0.5:
                categories["by_confidence"]["medium"] += 1
            else:
                categories["by_confidence"]["low"] += 1
            
            # Masking status
            if match.is_masked:
                categories["by_masking_status"]["masked"] += 1
            else:
                categories["by_masking_status"]["unmasked"] += 1
        
        return categories
    
    def _process_findings(self, matches: List[PANMatch]) -> List[dict]:
        """Process findings with appropriate privacy controls"""
        processed_findings = []
        
        for match in matches:
            finding = {
                "file_path": self._sanitize_file_path(match.file_path),
                "line_number": match.line_number,
                "column_range": [match.column_start, match.column_end],
                "card_type": match.card_type.value,
                "luhn_valid": match.luhn_valid,
                "confidence_score": round(match.confidence_score, 3),
                "is_masked": match.is_masked,
                "context": {
                    "before": self._sanitize_context(match.context_before),
                    "after": self._sanitize_context(match.context_after)
                },
                "remediation_priority": self._calculate_priority(match),
                "remediation_suggestions": self._get_remediation_suggestions(match)
            }
            
            # Handle PAN data based on privacy settings
            if self.allow_full_pan and not self.redact_pan:
                # Only include if explicitly authorized
                finding["pan_data"] = {
                    "full_number": match.raw_match,
                    "masked_number": match.masked_match,
                    "hash": hashlib.sha256(match.raw_match.encode()).hexdigest() if match.raw_match else None
                }
                logger.warning(f"Including full PAN in report for {match.file_path}:{match.line_number}")
            else:
                # Safe default - only masked/hashed data
                finding["pan_data"] = {
                    "masked_number": match.masked_match,
                    "hash": hashlib.sha256(match.raw_match.encode()).hexdigest() if match.raw_match else None
                }
            
            processed_findings.append(finding)
        
        return processed_findings
    
    def _sanitize_file_path(self, file_path: str) -> str:
        """Sanitize file paths to remove sensitive information"""
        # Remove username from path if present
        import re
        sanitized = re.sub(r'/Users/[^/]+/', '/Users/<user>/', file_path)
        sanitized = re.sub(r'\\Users\\[^\\]+\\', r'\\Users\\<user>\\', sanitized)
        sanitized = re.sub(r'C:\\Users\\[^\\]+\\', r'C:\\Users\\<user>\\', sanitized)
        return sanitized
    
    def _sanitize_context(self, context: str) -> str:
        """Remove potential sensitive data from context"""
        if not context:
            return ""
        
        # Remove potential email addresses
        import re
        sanitized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '<email>', context)
        
        # Remove potential SSNs
        sanitized = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '<ssn>', sanitized)
        
        # Limit context length
        if len(sanitized) > 200:
            sanitized = sanitized[:200] + "..."
        
        return sanitized
    
    def _calculate_priority(self, match: PANMatch) -> str:
        """Calculate remediation priority based on risk factors"""
        score = 0
        
        # High priority factors
        if match.luhn_valid:
            score += 3
        if not match.is_masked:
            score += 2
        if match.confidence_score > 0.8:
            score += 2
        if match.card_type in [CardType.VISA, CardType.MASTERCARD, CardType.AMEX]:
            score += 1
        
        if score >= 5:
            return "critical"
        elif score >= 3:
            return "high"
        elif score >= 1:
            return "medium"
        else:
            return "low"
    
    def _get_remediation_suggestions(self, match: PANMatch) -> List[str]:
        """Generate specific remediation suggestions"""
        suggestions = []
        
        if not match.is_masked and match.luhn_valid:
            suggestions.append("URGENT: Unmasked valid PAN detected - secure immediately")
        
        if match.luhn_valid:
            suggestions.append("Implement PAN masking or tokenization")
            suggestions.append("Review data retention policies")
            suggestions.append("Ensure PCI-DSS compliance for data handling")
        
        if match.confidence_score > 0.7:
            suggestions.append("High confidence match - verify and remediate")
        
        suggestions.append("Consider data encryption at rest")
        suggestions.append("Implement access controls and audit logging")
        
        return suggestions
    
    def _assess_risk(self, matches: List[PANMatch]) -> dict:
        """Assess overall risk based on findings"""
        if not matches:
            return {
                "overall_risk": "low",
                "risk_factors": [],
                "compliance_status": "compliant"
            }
        
        risk_factors = []
        high_risk_count = 0
        
        for match in matches:
            if match.luhn_valid and not match.is_masked:
                high_risk_count += 1
                risk_factors.append(f"Unmasked valid PAN in {match.file_path}")
        
        # Determine overall risk
        if high_risk_count > 0:
            overall_risk = "critical"
            compliance_status = "non-compliant"
        elif len(matches) > 10:
            overall_risk = "high"
            compliance_status = "review-required"
        elif len(matches) > 0:
            overall_risk = "medium"
            compliance_status = "review-required"
        else:
            overall_risk = "low"
            compliance_status = "compliant"
        
        return {
            "overall_risk": overall_risk,
            "risk_factors": risk_factors[:10],  # Limit to top 10
            "compliance_status": compliance_status,
            "total_high_risk_findings": high_risk_count
        }
    
    def _generate_recommendations(self, matches: List[PANMatch]) -> List[str]:
        """Generate high-level compliance recommendations"""
        recommendations = [
            "Implement regular PCI compliance scanning",
            "Establish data retention and disposal policies",
            "Implement strong access controls and authentication",
            "Enable comprehensive audit logging"
        ]
        
        if any(not match.is_masked and match.luhn_valid for match in matches):
            recommendations.insert(0, "CRITICAL: Secure unmasked PANs immediately")
            recommendations.insert(1, "Implement PAN masking/tokenization solution")
        
        if len(matches) > 5:
            recommendations.append("Consider automated PAN discovery and classification")
        
        return recommendations
    
    def export_csv(self, matches: List[PANMatch], file_path: str):
        """Export findings to CSV format for analysis"""
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'file_path', 'line_number', 'card_type', 'masked_number',
                'luhn_valid', 'confidence_score', 'is_masked', 'priority'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for match in matches:
                writer.writerow({
                    'file_path': self._sanitize_file_path(match.file_path),
                    'line_number': match.line_number,
                    'card_type': match.card_type.value,
                    'masked_number': match.masked_match,
                    'luhn_valid': match.luhn_valid,
                    'confidence_score': match.confidence_score,
                    'is_masked': match.is_masked,
                    'priority': self._calculate_priority(match)
                })
        
        logger.info(f"Exported {len(matches)} findings to CSV: {file_path}")