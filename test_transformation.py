"""
Test script to verify report transformation
"""
import json
import yaml
from main import PCIComplianceAgent

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize agent
agent = PCIComplianceAgent(config)

# Start a scan session
scan_id = agent.start_scan_session(operator='test_admin', directories=['./tests'])

# Run scan
matches = agent.run_scan()

# Generate report
report = agent.generate_report(matches)

# Show the original report structure
print("=== ORIGINAL REPORT STRUCTURE ===")
print(f"Top-level keys: {list(report.keys())}")
print(f"Metadata keys: {list(report.get('metadata', {}).keys())}")
print(f"Scan parameters keys: {list(report.get('scan_parameters', {}).keys())}")
print(f"Scan results keys: {list(report.get('scan_results', {}).keys())}")

# Transform the report
from secure_client import SecureClient
client = SecureClient(config)
transformed = client._transform_report_for_server(report)

# Show the transformed report structure
print("\n=== TRANSFORMED REPORT FOR SERVER ===")
print(f"Top-level keys: {list(transformed.keys())}")
print(f"\nRequired fields validation:")
print(f"  agent_id: {transformed.get('agent_id')} (type: {type(transformed.get('agent_id')).__name__})")
print(f"  operator: {transformed.get('operator')} (type: {type(transformed.get('operator')).__name__})")
print(f"  scan_date: {transformed.get('scan_date')} (type: {type(transformed.get('scan_date')).__name__})")
print(f"  directories_scanned: {transformed.get('directories_scanned')} (type: {type(transformed.get('directories_scanned')).__name__})")
print(f"  total_files_scanned: {transformed.get('total_files_scanned')} (type: {type(transformed.get('total_files_scanned')).__name__})")
print(f"  findings: length={len(transformed.get('findings', []))} (type: {type(transformed.get('findings')).__name__})")
print(f"  scan_configuration: {type(transformed.get('scan_configuration')).__name__}")

# Save the transformed report to see full structure
with open('transformed_report_test.json', 'w') as f:
    json.dump(transformed, f, indent=2, default=str)

print("\n✓ Transformed report saved to transformed_report_test.json")
