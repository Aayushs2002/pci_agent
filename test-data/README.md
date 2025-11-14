# PCI Compliance Test Data

This folder contains test files with simulated PCI compliance violations for testing the scanner.

## ⚠️ IMPORTANT: These are TEST CREDIT CARD NUMBERS ONLY

All credit card numbers in these files are:
- Standard test numbers used in payment processing development
- Will pass Luhn algorithm validation (checksum)
- **NOT real credit card numbers**
- Safe to use for testing purposes

## Test Files Included

### 1. `customer_orders.csv`
- CSV file with customer order data
- Contains multiple credit card numbers in different formats
- Includes both formatted (with dashes) and plain numbers

### 2. `payment_transactions.json`
- JSON format with transaction data
- Nested structure with payment method details
- Multiple card types (Visa, MasterCard, Amex)

### 3. `payment_logs.txt`
- Plain text log file
- Contains payment processing logs
- Mix of masked and unmasked card numbers

### 4. `payment_processor.py`
- Python source code file
- Contains test card numbers in code comments and variables
- Shows how PCI data might leak into source code

### 5. `database_backup.sql`
- SQL database dump
- Contains INSERT statements with credit card data
- Demonstrates database backup security risks

### 6. `payment_config.xml`
- XML configuration file
- Contains test card data in structured format
- Shows configuration file risks

### 7. `.env`
- Environment configuration file
- Contains secrets and test card numbers
- Common source of accidental PCI data exposure

## Expected Scan Results

When you scan this directory, the PCI compliance agent should detect:
- ✅ Multiple credit card numbers across different file types
- ✅ Various card types (Visa, MasterCard, American Express, Discover)
- ✅ Both formatted (with dashes/spaces) and unformatted numbers
- ✅ Numbers that pass Luhn validation

## Test Card Numbers Used

| Card Type | Number | Format |
|-----------|--------|--------|
| Visa | 4532123456789010 | Plain |
| Visa | 4532-1234-5678-9010 | Dashed |
| Visa | 4111111111111111 | Plain |
| MasterCard | 5425233430109903 | Plain |
| MasterCard | 5555-5555-5555-4444 | Dashed |
| American Express | 378282246310005 | Plain |
| Discover | 6011111111111117 | Plain |
| Discover | 6011-1111-1111-1117 | Dashed |

## How to Test

1. Start your GUI application
2. Navigate to the scan directory selection
3. Select this `test-data` folder
4. Run the scan
5. Verify that the agent detects the credit card numbers
6. Check the generated report for findings

## Expected Behavior

The scanner should:
- ✅ Find credit card numbers in all file types
- ✅ Validate them using Luhn algorithm
- ✅ Classify them by card type
- ✅ Mask the numbers in reports (showing only last 4 digits)
- ✅ Generate detailed compliance report
- ✅ Send results to the server

---

**Note**: After testing, you can delete this folder or keep it for future testing purposes.
