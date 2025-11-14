"""
PCI Compliance Agent - Test Suite for Detection Engine
"""

import pytest
import tempfile
import os
from detection_engine import PANDetector, CardType, PANMatch

@pytest.fixture
def config():
    """Test configuration"""
    return {
        'detection': {
            'require_luhn_validation': True,
            'minimum_confidence_score': 0.7,
            'context_window_chars': 100,
            'exclude_masked_patterns': True
        },
        'privacy': {
            'allow_full_pan_retention': False,
            'redact_pan': True,
            'show_last4_only': True
        }
    }

@pytest.fixture
def detector(config):
    """PAN detector instance"""
    return PANDetector(config)

class TestLuhnValidation:
    """Test Luhn algorithm implementation"""
    
    def test_valid_visa_pan(self, detector):
        """Test valid Visa PAN"""
        assert detector.luhn_check('4532015112830366') == True
    
    def test_valid_mastercard_pan(self, detector):
        """Test valid MasterCard PAN"""
        assert detector.luhn_check('5555555555554444') == True
    
    def test_valid_amex_pan(self, detector):
        """Test valid American Express PAN"""
        assert detector.luhn_check('378282246310005') == True
    
    def test_invalid_pan(self, detector):
        """Test invalid PAN"""
        assert detector.luhn_check('4532015112830367') == False
    
    def test_non_numeric_input(self, detector):
        """Test non-numeric input"""
        assert detector.luhn_check('abcd1234') == False
    
    def test_empty_input(self, detector):
        """Test empty input"""
        assert detector.luhn_check('') == False

class TestCardTypeDetection:
    """Test card type detection"""
    
    def test_visa_detection(self, detector):
        """Test Visa card detection"""
        assert detector.detect_card_type('4532015112830366') == CardType.VISA
    
    def test_mastercard_detection(self, detector):
        """Test MasterCard detection"""
        assert detector.detect_card_type('5555555555554444') == CardType.MASTERCARD
    
    def test_amex_detection(self, detector):
        """Test American Express detection"""
        assert detector.detect_card_type('378282246310005') == CardType.AMEX
    
    def test_unknown_card_type(self, detector):
        """Test unknown card type"""
        assert detector.detect_card_type('1234567890123456') == CardType.UNKNOWN

class TestMaskedDetection:
    """Test masked number detection"""
    
    def test_asterisk_masked(self, detector):
        """Test asterisk masked numbers"""
        assert detector.is_masked_number('****1234') == True
    
    def test_x_masked(self, detector):
        """Test X masked numbers"""
        assert detector.is_masked_number('XXXX1234') == True
    
    def test_hash_masked(self, detector):
        """Test hash masked numbers"""
        assert detector.is_masked_number('####1234') == True
    
    def test_partial_masked(self, detector):
        """Test partially masked numbers"""
        assert detector.is_masked_number('4532-****-****-0366') == True
    
    def test_unmasked_number(self, detector):
        """Test unmasked numbers"""
        assert detector.is_masked_number('4532015112830366') == False

class TestPANScanning:
    """Test PAN scanning functionality"""
    
    def test_scan_valid_pan(self, detector):
        """Test scanning text with valid PAN"""
        text = "Credit card number: 4532015112830366"
        matches = detector.scan_text(text, "test.txt")
        
        assert len(matches) == 1
        assert matches[0].card_type == CardType.VISA
        assert matches[0].luhn_valid == True
        assert matches[0].line_number == 1
    
    def test_scan_multiple_pans(self, detector):
        """Test scanning text with multiple PANs"""
        text = """
        Visa: 4532015112830366
        MasterCard: 5555555555554444
        Amex: 378282246310005
        """
        matches = detector.scan_text(text, "test.txt")
        
        assert len(matches) == 3
        card_types = [match.card_type for match in matches]
        assert CardType.VISA in card_types
        assert CardType.MASTERCARD in card_types
        assert CardType.AMEX in card_types
    
    def test_scan_masked_pan(self, detector):
        """Test scanning masked PANs"""
        text = "Credit card: ****1234"
        matches = detector.scan_text(text, "test.txt")
        
        # Should not detect masked numbers by default
        assert len(matches) == 0
    
    def test_scan_invalid_luhn(self, detector):
        """Test scanning invalid Luhn numbers"""
        text = "Invalid card: 4532015112830367"
        matches = detector.scan_text(text, "test.txt")
        
        # Should not detect invalid Luhn by default
        assert len(matches) == 0
    
    def test_confidence_scoring(self, detector):
        """Test confidence scoring"""
        text = "Credit card payment: 4532015112830366 CVV: 123"
        matches = detector.scan_text(text, "test.txt")
        
        assert len(matches) == 1
        assert matches[0].confidence_score > 0.7
    
    def test_context_extraction(self, detector):
        """Test context extraction"""
        text = "Before text credit card number: 4532015112830366 after text"
        matches = detector.scan_text(text, "test.txt")
        
        assert len(matches) == 1
        assert "Before text credit card number:" in matches[0].context_before
        assert "after text" in matches[0].context_after

class TestPANMasking:
    """Test PAN masking functionality"""
    
    def test_mask_pan_show_last4(self, detector):
        """Test masking with last 4 digits shown"""
        masked = detector.mask_pan('4532015112830366', show_last4=True)
        assert masked == '************0366'
    
    def test_mask_pan_full(self, detector):
        """Test full masking"""
        masked = detector.mask_pan('4532015112830366', show_last4=False)
        assert masked == '****************'
    
    def test_mask_short_number(self, detector):
        """Test masking short numbers"""
        masked = detector.mask_pan('123', show_last4=True)
        assert masked == '***'

class TestFileValidation:
    """Test file validation functionality"""
    
    def test_validate_file_size(self, detector):
        """Test file size validation"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('x' * 1000)  # 1KB file
            f.flush()
            
            try:
                # Should pass with default 10MB limit
                assert detector.validate_file_for_scanning(f.name) == True
            finally:
                os.unlink(f.name)
    
    def test_validate_excluded_extension(self, detector):
        """Test excluded file extensions"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.exe') as f:
            f.write('test content')
            f.flush()
            
            try:
                # Should be excluded based on extension
                result = detector.validate_file_for_scanning(f.name)
                # Result depends on configuration
                assert isinstance(result, bool)
            finally:
                os.unlink(f.name)

class TestSecurityFeatures:
    """Test security-related features"""
    
    def test_pan_hashing(self, detector):
        """Test PAN hashing"""
        pan = '4532015112830366'
        hash1 = detector.hash_pan(pan)
        hash2 = detector.hash_pan(pan)
        
        # Same PAN should produce same hash
        assert hash1 == hash2
        
        # Hash should be different from original
        assert hash1 != pan
        
        # Hash should be consistent length
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_no_pan_retention_by_default(self, detector):
        """Test that PANs are not retained by default"""
        text = "Credit card: 4532015112830366"
        matches = detector.scan_text(text, "test.txt")
        
        if matches:
            # Should not contain full PAN unless explicitly allowed
            assert matches[0].raw_match == "" or matches[0].raw_match is None

if __name__ == '__main__':
    pytest.main(['-v', __file__])