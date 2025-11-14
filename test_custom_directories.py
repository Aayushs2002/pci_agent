"""
Test script to verify custom directory scanning works
"""
import yaml
from main import PCIComplianceAgent

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize agent
agent = PCIComplianceAgent('config.yaml')

# Test with custom directory
custom_dirs = ['C:\\Windows\\System32\\drivers\\etc']
print(f"Testing scan with custom directories: {custom_dirs}")

# Start scan session with custom directories
scan_id = agent.start_scan_session('test_operator', custom_dirs)
print(f"✓ Scan started with ID: {scan_id}")
print(f"✓ Agent is configured to scan: {agent.current_directories}")

# Run the scan
matches = agent.run_scan()
print(f"✓ Scan complete! Found {len(matches)} matches")

# Generate report
report = agent.generate_report(matches)
print(f"✓ Report generated")
print(f"✓ Report shows scanned directories: {report['actual_directories']}")

# Verify the directories match
if report['actual_directories'] == custom_dirs:
    print("\n✅ SUCCESS! Custom directories are being used correctly!")
else:
    print(f"\n❌ FAILED! Expected {custom_dirs} but got {report['actual_directories']}")
