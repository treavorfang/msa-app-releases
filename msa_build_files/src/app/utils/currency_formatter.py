# src/app/utils/currency_formatter.py
"""
Currency Formatter Utility
Provides consistent currency formatting based on language settings.
"""

from utils.language_manager import language_manager


class CurrencyFormatter:
    """Singleton class for formatting currency values based on language settings"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CurrencyFormatter, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.lm = language_manager
        self._load_currency_settings()
    
    def _load_currency_settings(self):
        """Load currency settings from current language or overrides"""
        self.symbol = self.lm.get("Currency.symbol", "$")
        self.code = self.lm.get("Currency.code", "USD")
        self.name = self.lm.get("Currency.name", "US Dollar")
        self.position = self.lm.get("Currency.position", "before")
        self.decimal_separator = self.lm.get("Currency.decimal_separator", ".")
        self.thousands_separator = self.lm.get("Currency.thousands_separator", ",")
        self.decimal_places = int(self.lm.get("Currency.decimal_places", "2"))
        
        # Checking for manual overrides (from settings)
        if hasattr(self, '_overrides') and self._overrides:
            if 'symbol' in self._overrides: self.symbol = self._overrides['symbol']
            if 'code' in self._overrides: self.code = self._overrides['code']
            if 'position' in self._overrides: self.position = self._overrides['position']
            # Add others as needed
            
    def set_currency_overrides(self, code, symbol=None):
        """
        Manually set currency, overriding language defaults.
        Call this when loading app settings.
        """
        self._overrides = {'code': code}
        
        # Simple mapping for common currencies if symbol not provided
        # Ideally this should be more robust
        symbols = {
            'USD': '$',
            'MMK': 'Ks', # Or 'K' or 'Ks '
            'EUR': '€',
            'GBP': '£'
        }
        
        if symbol:
            self._overrides['symbol'] = symbol
        else:
            self._overrides['symbol'] = symbols.get(code, code)
            
        if code == 'MMK':
             self._overrides['position'] = 'after'
             self._overrides['decimal_places'] = 0
        else:
             self._overrides['position'] = 'before'
             
        self._load_currency_settings()
        
    def reload(self):
        """Reload currency settings (call after language change)"""
        self._load_currency_settings()
    
    def format(self, amount, show_symbol=True, show_code=False):
        """
        Format amount with current currency settings
        
        Args:
            amount: Numeric value to format
            show_symbol: Whether to show currency symbol (default: True)
            show_code: Whether to show currency code instead of symbol (default: False)
        
        Returns:
            Formatted currency string
        
        Examples:
            format(1234.56) -> "$1,234.56" (USD)
            format(1234.56) -> "1,235 Ks" (MMK, no decimals)
            format(1234.56, show_code=True) -> "1,234.56 USD"
        """
        try:
            # Convert to float
            value = float(amount)
            
            # Format with proper decimal places
            if self.decimal_places == 0:
                # Round to nearest integer for currencies without decimals (like MMK)
                value = round(value)
                formatted_number = f"{int(value):,}"
            else:
                formatted_number = f"{value:,.{self.decimal_places}f}"
            
            # Replace separators if needed (for locales that use different separators)
            if self.thousands_separator != ",":
                formatted_number = formatted_number.replace(",", "TEMP")
                formatted_number = formatted_number.replace(".", self.decimal_separator)
                formatted_number = formatted_number.replace("TEMP", self.thousands_separator)
            elif self.decimal_separator != ".":
                formatted_number = formatted_number.replace(".", self.decimal_separator)
            
            # Add currency symbol or code
            if not show_symbol and not show_code:
                return formatted_number
            
            currency_indicator = self.code if show_code else self.symbol
            
            if self.position == "before":
                return f"{currency_indicator}{formatted_number}"
            else:  # after
                return f"{formatted_number} {currency_indicator}"
                
        except (ValueError, TypeError):
            # Fallback for invalid input
            return f"{self.symbol}0.00" if show_symbol else "0.00"
    
    def format_with_sign(self, amount):
        """
        Format amount with +/- sign for positive/negative values
        Useful for displaying balances, credits, debits
        
        Examples:
            format_with_sign(100) -> "+$100.00"
            format_with_sign(-50) -> "-$50.00"
            format_with_sign(0) -> "$0.00"
        """
        try:
            value = float(amount)
            if value > 0:
                return f"+{self.format(value)}"
            elif value < 0:
                return f"-{self.format(abs(value))}"
            else:
                return self.format(0)
        except (ValueError, TypeError):
            return self.format(0)
    
    def get_currency_symbol(self):
        """Get the current currency symbol"""
        return self.symbol

    def parse(self, formatted_string):
        """
        Parse a formatted currency string back to a float
        
        Args:
            formatted_string: String like "$1,234.56" or "1,234.56 USD"
            
        Returns:
            float value
        """
        if not formatted_string:
            return 0.0
            
        try:
            # Remove symbol and code
            clean_str = formatted_string.replace(self.symbol, "").replace(self.code, "").strip()
            
            # Handle negative sign
            is_negative = "-" in clean_str
            clean_str = clean_str.replace("-", "").replace("+", "")
            
            # Remove thousands separator
            if self.thousands_separator:
                clean_str = clean_str.replace(self.thousands_separator, "")
            
            # Replace decimal separator with dot if different
            if self.decimal_separator != ".":
                clean_str = clean_str.replace(self.decimal_separator, ".")
                
            # Remove any other non-numeric characters except dot
            clean_str = ''.join(c for c in clean_str if c.isdigit() or c == '.')
            
            value = float(clean_str) if clean_str else 0.0
            
            return -value if is_negative else value
            
        except (ValueError, TypeError):
            return 0.0

    def get_currency_info(self):
        """Get current currency information as a dictionary"""
        return {
            'symbol': self.symbol,
            'code': self.code,
            'name': self.name,
            'position': self.position,
            'decimal_places': self.decimal_places,
            'decimal_separator': self.decimal_separator,
            'thousands_separator': self.thousands_separator
        }


# Global singleton instance
currency_formatter = CurrencyFormatter()
