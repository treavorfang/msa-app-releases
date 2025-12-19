import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'app')))

from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

def test_currency_formatter():
    print("=" * 60)
    print("CURRENCY FORMATTER TEST")
    print("=" * 60)
    
    # Test with English (USD)
    print("\n1. Testing with English (USD):")
    print("-" * 60)
    language_manager.load_language("English")
    currency_formatter.reload()
    
    info = currency_formatter.get_currency_info()
    print(f"Currency: {info['name']} ({info['code']})")
    print(f"Symbol: {info['symbol']}, Position: {info['position']}")
    print(f"Decimal places: {info['decimal_places']}")
    
    test_amounts = [0, 1234.56, -500.75, 1000000, 0.99]
    print("\nFormatted amounts:")
    for amount in test_amounts:
        formatted = currency_formatter.format(amount)
        with_sign = currency_formatter.format_with_sign(amount)
        print(f"  {amount:>12} → {formatted:>15} (with sign: {with_sign})")
    
    # Test with Burmese (MMK)
    print("\n2. Testing with Burmese (MMK):")
    print("-" * 60)
    language_manager.load_language("Burmese")
    currency_formatter.reload()
    
    info = currency_formatter.get_currency_info()
    print(f"Currency: {info['name']} ({info['code']})")
    print(f"Symbol: {info['symbol']}, Position: {info['position']}")
    print(f"Decimal places: {info['decimal_places']}")
    
    print("\nFormatted amounts:")
    for amount in test_amounts:
        formatted = currency_formatter.format(amount)
        with_sign = currency_formatter.format_with_sign(amount)
        with_code = currency_formatter.format(amount, show_code=True)
        print(f"  {amount:>12} → {formatted:>15} (code: {with_code})")
    
    # Test edge cases
    print("\n3. Testing edge cases:")
    print("-" * 60)
    edge_cases = [None, "invalid", "", 0.001, 999999999.99]
    for value in edge_cases:
        try:
            formatted = currency_formatter.format(value)
            print(f"  {str(value):>12} → {formatted}")
        except Exception as e:
            print(f"  {str(value):>12} → ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_currency_formatter()
