# src/app/utils/format/phone_formatter.py
import phonenumbers
from typing import Optional
import re

class PhoneFormatter:
    """Handles phone number formatting using phonenumbers library with generic fallback formatting."""
    
    def __init__(self, default_region: str = "MM"):  # Default to Myanmar
        self.default_region = default_region
    
    def format_phone_number(self, phone: str) -> str:
        """
        Format phone number for display. Does NOT auto-add country code to local numbers.
        Returns formatted string or original if formatting fails.
        """
        if not phone:
            return ""
        
        phone = phone.strip()
        
        # First try with phonenumbers library for proper international formatting
        # Only use this for numbers that explicitly start with +
        if phone.startswith('+'):
            try:
                # Clean the phone number - remove any non-digit characters except +
                cleaned_phone = re.sub(r'[^\d+]', '', phone)
                parsed = phonenumbers.parse(cleaned_phone, None)
                formatted = phonenumbers.format_number(
                    parsed, 
                    phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
                return formatted
            except (phonenumbers.NumberParseException, Exception):
                # If phonenumbers fails, use generic formatting but keep the +
                return self._generic_format(phone, is_international=True)
        
        # For local numbers (without +), use generic formatting without adding country code
        return self._generic_format(phone, is_international=False)
    
    def _generic_format(self, phone: str, is_international: bool = False) -> str:
        """
        Generic phone number formatting that works for most numbers.
        Does NOT auto-add country code for local numbers.
        """
        if not phone:
            return ""
        
        # Extract digits only
        digits = ''.join(c for c in phone if c.isdigit())
        
        if not digits:
            return phone  # Return original if no digits found
        
        # For international numbers starting with +, preserve the + and format
        if is_international:
            # Try to extract country code for better formatting
            country_code = self._detect_country_code(digits)
            if country_code:
                remaining_digits = digits[len(country_code):]
                formatted_remaining = self._format_digits(remaining_digits)
                return f"+{country_code} {formatted_remaining}"
            else:
                # Just format all digits with + prefix
                return f"+{self._format_digits(digits)}"
        
        # For local numbers, just format the digits without adding country code
        return self._format_digits(digits)
    
    def _format_digits(self, digits: str) -> str:
        """
        Format digits with intelligent grouping based on length.
        """
        length = len(digits)
        
        if length <= 4:
            return digits
        
        elif length == 5:
            return f"{digits[:2]} {digits[2:]}"
        
        elif length == 6:
            return f"{digits[:3]} {digits[3:]}"
        
        elif length == 7:
            return f"{digits[:3]} {digits[3:]}"
        
        elif length == 8:
            return f"{digits[:4]} {digits[4:]}"
        
        elif length == 9:
            return f"{digits[:3]} {digits[3:6]} {digits[6:]}"
        
        elif length == 10:
            return f"{digits[:3]} {digits[3:6]} {digits[6:]}"
        
        elif length == 11:
            return f"{digits[:4]} {digits[4:7]} {digits[7:]}"
        
        else:
            # For very long numbers, group in chunks of 3-4 digits
            formatted = []
            i = 0
            while i < length:
                # Prefer 4-digit chunks after the first group if possible
                if i == 0 and length > 7:
                    chunk_size = 4 if (length - i) % 4 == 0 or (length - i) > 8 else 3
                else:
                    chunk_size = 3 if (length - i) % 3 == 0 or (length - i) < 4 else 4
                
                chunk = digits[i:i + chunk_size]
                formatted.append(chunk)
                i += chunk_size
            
            return ' '.join(formatted)
    
    def _detect_country_code(self, digits: str) -> Optional[str]:
        """
        Detect country code from digits (only for international numbers).
        """
        if not digits:
            return None
        
        # Common country code patterns (1-3 digits)
        common_country_codes = {
            '1', '7', '20', '27', '30', '31', '32', '33', '34', '36', '39', '40',
            '41', '43', '44', '45', '46', '47', '48', '49', '51', '52', '53', '54',
            '55', '56', '57', '58', '60', '61', '62', '63', '64', '65', '66', '81',
            '82', '84', '86', '90', '91', '92', '93', '94', '95', '98', '212', '213',
            '216', '218', '220', '221', '222', '223', '224', '225', '226', '227',
            '228', '229', '230', '231', '232', '233', '234', '235', '236', '237',
            '238', '239', '240', '241', '242', '243', '244', '245', '246', '247',
            '248', '249', '250', '251', '252', '253', '254', '255', '256', '257',
            '258', '260', '261', '262', '263', '264', '265', '266', '267', '268',
            '269', '290', '291', '297', '298', '299', '350', '351', '352', '353',
            '354', '355', '356', '357', '358', '359', '370', '371', '372', '373',
            '374', '375', '376', '377', '378', '379', '380', '381', '382', '383',
            '385', '386', '387', '389', '420', '421', '423', '500', '501', '502',
            '503', '504', '505', '506', '507', '508', '509', '590', '591', '592',
            '593', '594', '595', '596', '597', '598', '599', '670', '672', '673',
            '674', '675', '676', '677', '678', '679', '680', '681', '682', '683',
            '685', '686', '687', '688', '689', '690', '691', '692', '850', '852',
            '853', '855', '856', '880', '886', '960', '961', '962', '963', '964',
            '965', '966', '967', '968', '970', '971', '972', '973', '974', '975',
            '976', '977', '992', '993', '994', '995', '996', '998'
        }
        
        # Check for 1-digit country codes
        if digits[:1] in common_country_codes:
            return digits[:1]
        
        # Check for 2-digit country codes
        if len(digits) >= 2 and digits[:2] in common_country_codes:
            return digits[:2]
        
        # Check for 3-digit country codes
        if len(digits) >= 3 and digits[:3] in common_country_codes:
            return digits[:3]
        
        return None
    
    def set_default_region(self, region_code: str) -> None:
        """Set the default region for parsing local numbers."""
        self.default_region = region_code.upper()
    
    def is_valid_phone(self, phone: str) -> bool:
        """Check if a phone number is valid."""
        if not phone:
            return False
        
        # Basic validation - at least 7 digits
        digits = ''.join(c for c in phone if c.isdigit())
        return len(digits) >= 7

# Global instance for easy access
phone_formatter = PhoneFormatter("MM")