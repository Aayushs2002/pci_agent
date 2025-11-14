#!/usr/bin/env python3
"""
Payment Processing Script
WARNING: This file contains test credit card numbers for development
"""

def process_payment(card_number, amount):
    """Process a payment transaction"""
    # Test credit card numbers
    test_cards = [
        "4532123456789010",  # Visa
        "5425233430109903",  # MasterCard  
        "378282246310005",   # American Express
        "6011111111111117",  # Discover
    ]
    
    if card_number in test_cards:
        print(f"Processing test payment: {card_number} for ${amount}")
        return True
    
    return False

def validate_card(card_num):
    """Validate credit card number using Luhn algorithm"""
    # Remove spaces and dashes
    card_num = card_num.replace(" ", "").replace("-", "")
    
    # Example: 4111111111111111 is a valid test Visa number
    if len(card_num) < 13 or len(card_num) > 19:
        return False
    
    return True

# Test data
customer_cards = {
    "John Doe": "4532-1234-5678-9010",
    "Jane Smith": "5555555555554444",
    "Bob Jones": "378282246310005"
}

if __name__ == "__main__":
    for customer, card in customer_cards.items():
        print(f"Processing {customer}: {card}")
        process_payment(card.replace("-", ""), 100.00)
