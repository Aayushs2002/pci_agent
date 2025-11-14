"""
PCI Compliance Agent - PAN Detection Engine
Secure detection of Payment Card Numbers with Luhn validation
"""

import re
import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import hashlib
import os

logger = logging.getLogger(__name__)

class CardType(Enum):
    VISA = "visa"
    MASTERCARD = "mastercard"
    AMEX = "amex"
    DISCOVER = "discover"
    DINERS = "diners"
    JCB = "jcb"
    UNKNOWN = "unknown"

@dataclass
class PANMatch:
    """Represents a potential PAN match in a file"""
    file_path: str
    line_number: int
    column_start: int
    column_end: int
    raw_match: str
    masked_match: str
    card_type: CardType
    luhn_valid: bool
    confidence_score: float
    context_before: str
    context_after: str
    is_masked: bool

class PANDetector:
    """Core PAN detection engine with Luhn validation and masking detection"""
    
    # Card type patterns - comprehensive regex for major card brands
    CARD_PATTERNS = {
        CardType.VISA: r'4[0-9]{12}(?:[0-9]{3})?',
        CardType.MASTERCARD: r'5[1-5][0-9]{14}|2(?:2(?:2[1-9]|[3-9][0-9])|[3-6][0-9][0-9]|7(?:[0-1][0-9]|20))[0-9]{12}',
        CardType.AMEX: r'3[47][0-9]{13}',
        CardType.DISCOVER: r'6(?:011|5[0-9]{2})[0-9]{12}',
        CardType.DINERS: r'3(?:0[0-5]|[68][0-9])[0-9]{11}',
        CardType.JCB: r'(?:2131|1800|35\d{3})\d{11}'
    }
    
    # Patterns that indicate masked/redacted numbers
    MASKED_PATTERNS = [
        r'\*{4,}',          # ****1234
        r'X{4,}',           # XXXX1234
        r'#{4,}',           # ####1234
        r'\*+\d{4}',        # ***1234
        r'X+\d{4}',         # XXX1234
        r'#+\d{4}',         # ###1234
        r'\d{4}[\*X#]{4,}', # 1234****
        r'\d{4}-\*{4}-\*{4}-\d{4}',  # 1234-****-****-1234
    ]
    
    def __init__(self, config: dict):
        """Initialize detector with configuration"""
        self.config = config
        self.require_luhn = config.get('detection', {}).get('require_luhn_validation', True)
        self.min_confidence = config.get('detection', {}).get('minimum_confidence_score', 0.7)
        self.context_window = config.get('detection', {}).get('context_window_chars', 100)
        self.exclude_masked = config.get('detection', {}).get('exclude_masked_patterns', True)
        
        # Compile regex patterns for performance
        self._compile_patterns()
        
        logger.info(f"PANDetector initialized with Luhn validation: {self.require_luhn}")
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        self.compiled_patterns = {}
        for card_type, pattern in self.CARD_PATTERNS.items():
            self.compiled_patterns[card_type] = re.compile(r'\b' + pattern + r'\b')
        
        self.masked_regex = [re.compile(pattern) for pattern in self.MASKED_PATTERNS]
        logger.debug(f"Compiled {len(self.compiled_patterns)} card patterns and {len(self.masked_regex)} mask patterns")
    
    def luhn_check(self, card_number: str) -> bool:
        """
        Validate card number using Luhn algorithm
        Returns True if valid, False otherwise
        """
        # Remove any non-digit characters
        digits = [int(d) for d in card_number if d.isdigit()]
        
        if len(digits) < 13 or len(digits) > 19:
            return False
        
        checksum = 0
        parity = len(digits) % 2
        
        for i, digit in enumerate(digits):
            if i % 2 == parity:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        
        return checksum % 10 == 0
    
    def is_masked_number(self, text: str) -> bool:
        """Check if the text appears to be a masked card number"""
        if not self.exclude_masked:
            return False
            
        for regex in self.masked_regex:
            if regex.search(text):
                return True
        return False
    
    def mask_pan(self, pan: str, show_last4: bool = True) -> str:
        """
        Mask PAN for safe display - shows only last 4 digits by default
        """
        if len(pan) < 4:
            return "*" * len(pan)
        
        if show_last4:
            return "*" * (len(pan) - 4) + pan[-4:]
        else:
            return "*" * len(pan)
    
    def hash_pan(self, pan: str) -> str:
        """Create SHA256 hash of PAN for secure storage"""
        return hashlib.sha256(pan.encode()).hexdigest()
    
    def calculate_confidence(self, match: str, card_type: CardType, luhn_valid: bool, 
                           context: str, is_masked: bool) -> float:
        """
        Calculate confidence score for a PAN match
        Factors: Luhn validation, context clues, card type validity, masking
        """
        confidence = 0.0
        
        # Base confidence for pattern match
        confidence += 0.3
        
        # Luhn validation adds significant confidence
        if luhn_valid:
            confidence += 0.4
        
        # Context analysis - look for payment-related keywords
        payment_keywords = [
            'card', 'credit', 'debit', 'payment', 'visa', 'mastercard', 'amex',
            'discover', 'pan', 'account', 'number', 'cvv', 'expiry', 'expire'
        ]
        
        context_lower = context.lower()
        keyword_matches = sum(1 for keyword in payment_keywords if keyword in context_lower)
        confidence += min(keyword_matches * 0.05, 0.2)
        
        # Penalize if it appears to be masked (lower risk)
        if is_masked:
            confidence -= 0.2
        
        # Bonus for known major card types
        if card_type in [CardType.VISA, CardType.MASTERCARD, CardType.AMEX]:
            confidence += 0.1
        
        return min(max(confidence, 0.0), 1.0)
    
    def detect_card_type(self, pan: str) -> CardType:
        """Determine card type based on number pattern"""
        digits_only = re.sub(r'\D', '', pan)
        
        for card_type, pattern in self.compiled_patterns.items():
            if pattern.match(digits_only):
                return card_type
        
        return CardType.UNKNOWN
    
    def scan_text(self, text: str, file_path: str) -> List[PANMatch]:
        """
        Scan text content for potential PANs
        Returns list of PANMatch objects
        """
        matches = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Skip lines that appear to contain only masked numbers
            if self.is_masked_number(line):
                logger.debug(f"Skipping masked line at {file_path}:{line_num}")
                continue
            
            # Check each card type pattern
            for card_type, pattern in self.compiled_patterns.items():
                for match in pattern.finditer(line):
                    pan_candidate = match.group()
                    digits_only = re.sub(r'\D', '', pan_candidate)
                    
                    # Skip if too short or too long
                    if len(digits_only) < 13 or len(digits_only) > 19:
                        continue
                    
                    # Luhn validation
                    luhn_valid = self.luhn_check(digits_only)
                    
                    # Skip if Luhn validation required but failed
                    if self.require_luhn and not luhn_valid:
                        continue
                    
                    # Extract context
                    start_pos = max(0, match.start() - self.context_window)
                    end_pos = min(len(line), match.end() + self.context_window)
                    
                    context_before = line[start_pos:match.start()]
                    context_after = line[match.end():end_pos]
                    full_context = context_before + pan_candidate + context_after
                    
                    # Check if this specific match appears masked
                    is_masked = self.is_masked_number(full_context)
                    
                    # Calculate confidence score
                    confidence = self.calculate_confidence(
                        pan_candidate, card_type, luhn_valid, full_context, is_masked
                    )
                    
                    # Skip low confidence matches
                    if confidence < self.min_confidence:
                        continue
                    
                    # Create masked version for safe storage
                    show_last4 = self.config.get('privacy', {}).get('show_last4_only', True)
                    masked_pan = self.mask_pan(digits_only, show_last4)
                    
                    pan_match = PANMatch(
                        file_path=file_path,
                        line_number=line_num,
                        column_start=match.start(),
                        column_end=match.end(),
                        raw_match=pan_candidate if self.config.get('privacy', {}).get('allow_full_pan_retention', False) else "",
                        masked_match=masked_pan,
                        card_type=card_type,
                        luhn_valid=luhn_valid,
                        confidence_score=confidence,
                        context_before=context_before[-50:] if len(context_before) > 50 else context_before,
                        context_after=context_after[:50] if len(context_after) > 50 else context_after,
                        is_masked=is_masked
                    )
                    
                    matches.append(pan_match)
                    
                    logger.debug(f"Found PAN candidate: {file_path}:{line_num} "
                               f"Type: {card_type.value} Luhn: {luhn_valid} "
                               f"Confidence: {confidence:.2f}")
        
        return matches
    
    def validate_file_for_scanning(self, file_path: str) -> bool:
        """
        Check if file should be scanned based on configuration
        """
        try:
            # Check file size
            max_size = self.config.get('agent', {}).get('max_file_size_mb', 10) * 1024 * 1024
            if os.path.getsize(file_path) > max_size:
                logger.debug(f"Skipping {file_path}: exceeds size limit")
                return False
            
            # Check file extension
            scan_extensions = self.config.get('agent', {}).get('file_extensions_to_scan', [])
            if scan_extensions:
                file_ext = os.path.splitext(file_path)[1].lower()
                if file_ext not in scan_extensions:
                    logger.debug(f"Skipping {file_path}: extension {file_ext} not in scan list")
                    return False
            
            return True
            
        except (OSError, IOError) as e:
            logger.warning(f"Cannot access file {file_path}: {e}")
            return False
    
    def get_detection_stats(self) -> Dict[str, int]:
        """Return statistics about detection patterns"""
        return {
            'card_patterns': len(self.CARD_PATTERNS),
            'masked_patterns': len(self.MASKED_PATTERNS),
            'min_confidence': self.min_confidence,
            'luhn_required': self.require_luhn
        }