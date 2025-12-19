# src/app/utils/validation/input_validator.py
import re
from Levenshtein import distance as levenshtein_distance
from PySide6.QtCore import QObject, QDate
from typing import Tuple, Optional, Union, Dict
from datetime import datetime

class InputValidator(QObject):
    """A comprehensive validator class for various input validations."""
    
    # Class constants
    POPULAR_DOMAINS = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'protonmail.com']
    EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(\.[a-zA-Z]{2,})?$"
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    
    # Enhanced common passwords list
    COMMON_PASSWORDS = [
        'password', '123456', 'qwerty', 'letmein', 'admin', 'welcome',
        'password123', 'passw0rd', '123456789', '12345678', '12345',
        '111111', 'sunshine', 'iloveyou', 'monkey', 'abc123', 'football',
        'admin123', 'welcome123', 'password1', '123123', '000000'
    ]
    
    # Password complexity requirements
    COMPLEXITY_REQUIREMENTS = {
        'min_length': MIN_PASSWORD_LENGTH,
        'require_upper': True,
        'require_lower': True,
        'require_digit': True,
        'require_special': True,
        'max_consecutive': 3,
        'min_unique': 5,
    }

    @staticmethod
    def validate_password_complexity(password: str) -> Dict[str, Tuple[bool, str]]:
        """Comprehensive password complexity validation with detailed feedback."""
        results = {}
        
        if not password:
            return {
                'length': (False, f"Minimum {InputValidator.MIN_PASSWORD_LENGTH} characters"),
                'max_length': (True, f"Maximum {InputValidator.MAX_PASSWORD_LENGTH} characters"),
                'upper': (False, "At least one uppercase letter"),
                'lower': (False, "At least one lowercase letter"),
                'digit': (False, "At least one digit"),
                'special': (False, "At least one special character"),
                'consecutive': (True, "No more than 3 consecutive identical characters"),
                'unique': (False, f"At least {InputValidator.COMPLEXITY_REQUIREMENTS['min_unique']} unique characters"),
                'common': (True, "Not a commonly used password"),
                'sequential': (True, "No sequential characters (e.g., '1234', 'abcd')"),
            }
        
        # Length check
        results['length'] = (
            len(password) >= InputValidator.MIN_PASSWORD_LENGTH,
            f"Minimum {InputValidator.MIN_PASSWORD_LENGTH} characters"
        )
        
        # Maximum length
        results['max_length'] = (
            len(password) <= InputValidator.MAX_PASSWORD_LENGTH,
            f"Maximum {InputValidator.MAX_PASSWORD_LENGTH} characters"
        )
        
        # Character diversity
        results['upper'] = (
            any(c.isupper() for c in password),
            "At least one uppercase letter"
        )
        
        results['lower'] = (
            any(c.islower() for c in password),
            "At least one lowercase letter"
        )
        
        results['digit'] = (
            any(c.isdigit() for c in password),
            "At least one digit"
        )
        
        results['special'] = (
            any(not c.isalnum() for c in password),
            "At least one special character"
        )
        
        # Consecutive characters check
        consecutive_chars = any(
            password[i] == password[i+1] == password[i+2] == password[i+3]
            for i in range(len(password) - 3)
        )
        results['consecutive'] = (
            not consecutive_chars,
            "No more than 3 consecutive identical characters"
        )
        
        # Unique characters
        unique_chars = len(set(password))
        results['unique'] = (
            unique_chars >= InputValidator.COMPLEXITY_REQUIREMENTS['min_unique'],
            f"At least {InputValidator.COMPLEXITY_REQUIREMENTS['min_unique']} unique characters"
        )
        
        # Common password check
        is_common = password.lower() in InputValidator.COMMON_PASSWORDS
        results['common'] = (
            not is_common,
            "Not a commonly used password"
        )
        
        # Sequential characters (e.g., "1234", "abcd")
        sequential = any(
            ord(password[i+1]) - ord(password[i]) == 1 and
            ord(password[i+2]) - ord(password[i+1]) == 1 and
            ord(password[i+3]) - ord(password[i+2]) == 1
            for i in range(len(password) - 3)
        )
        results['sequential'] = (
            not sequential,
            "No sequential characters (e.g., '1234', 'abcd')"
        )
        
        return results

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """Strong password validation with detailed feedback."""
        password = password.strip()
        
        # Basic length check
        if len(password) < InputValidator.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {InputValidator.MIN_PASSWORD_LENGTH} characters"
        
        if len(password) > InputValidator.MAX_PASSWORD_LENGTH:
            return False, f"Password must not exceed {InputValidator.MAX_PASSWORD_LENGTH} characters"
        
        # Check against common passwords
        if password.lower() in InputValidator.COMMON_PASSWORDS:
            return False, "Password is too common and easily guessable"
        
        # Comprehensive complexity check
        complexity = InputValidator.validate_password_complexity(password)
        
        # Check for any failed requirements
        failed_requirements = [
            message for req, (is_valid, message) in complexity.items() 
            if not is_valid
        ]
        
        if failed_requirements:
            return False, f"Password requirements not met: {', '.join(failed_requirements[:3])}"
        
        return True, "Password is strong and secure"

    @staticmethod
    def is_probable_typo(domain: str) -> Tuple[bool, Optional[str]]:
        """Check if a domain is likely a typo of a popular email provider."""
        domain_parts = domain.split('.')
        if len(domain_parts) < 2:
            return False, None
            
        domain_root = domain_parts[0]
        
        for popular in InputValidator.POPULAR_DOMAINS:
            popular_root = popular.split('.')[0]
            dist = levenshtein_distance(domain_root, popular_root)
            
            # Consider it a typo if within 2 edits and not exact match
            if dist <= 2 and domain_root != popular_root:
                suggested_domain = f"{popular_root}.{'.'.join(domain_parts[1:])}"
                return True, suggested_domain
                
        return False, None

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Comprehensive email validation with detailed error reporting."""
        email = email.strip().lower()
        
        # Basic format check
        if not re.match(InputValidator.EMAIL_REGEX, email):
            return False, "Invalid email format. Please use name@domain.com"
        
        # Extract domain
        domain = email.split('@')[-1]
        
        # Check for typos
        is_typo, suggestion = InputValidator.is_probable_typo(domain)
        if is_typo:
            return False, f"Possible typo in email domain. Did you mean {suggestion}?"
            
        return True, "Email is valid"
    
    @staticmethod
    def validate_email_and_password(email: str, password: str) -> Tuple[bool, str]:
        """Convenience method to validate both email and password."""
        email_valid, email_msg = InputValidator.validate_email(email)
        if not email_valid:
            return False, email_msg
            
        password_valid, password_msg = InputValidator.validate_password(password)
        if not password_valid:
            return False, password_msg
            
        return True, "Both email and password are valid"
    
    @staticmethod
    def validate_name(name: str, min_length: int = 2, max_length: int = 100) -> bool:
        """Validate person/business names."""
        if not name:
            return False
        name = name.strip()
        # Allow any characters for multi-language support (removed strict alpha checks)
        return min_length <= len(name) <= max_length 
        # and all(c.isalpha() or c.isspace() or c in ("-", "'") for c in name))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        Validate phone number format (international numbers supported)
        Returns True if valid, False otherwise
        """
        if not phone:
            return False
            
        # Basic pattern that allows:
        # - Optional + prefix
        # - Numbers, spaces, hyphens, parentheses
        pattern = r"^\+?[\d\s\-\(\)]{7,}$"
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_device_model(model: str) -> bool:
        """Validate device model (2-50 alphanumeric characters with spaces and common symbols)"""
        if not model or len(model) < 2 or len(model) > 50:
            return False
        # Allow alphanumeric, spaces, and common symbols like -, +, ., _, (), []
        return bool(re.match(r'^[a-zA-Z0-9\s\-+._()\[\]]+$', model))
    
    @staticmethod
    def validate_date(date: Union[str, QDate], 
                     min_date: Optional[Union[str, QDate]] = None,
                     max_date: Optional[Union[str, QDate]] = None) -> bool:
        """
        Validate date format and range
        Accepts either string (YYYY-MM-DD) or QDate objects
        """
        try:
            # Convert to datetime.date for comparison
            if isinstance(date, QDate):
                dt = date.toPython()
            else:
                dt = datetime.strptime(date, "%Y-%m-%d").date()
                
            # Check min date
            if min_date:
                if isinstance(min_date, QDate):
                    min_dt = min_date.toPython()
                else:
                    min_dt = datetime.strptime(min_date, "%Y-%m-%d").date()
                if dt < min_dt:
                    return False
                    
            # Check max date
            if max_date:
                if isinstance(max_date, QDate):
                    max_dt = max_date.toPython()
                else:
                    max_dt = datetime.strptime(max_date, "%Y-%m-%d").date()
                if dt > max_dt:
                    return False
                    
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_price(price: Union[str, float, int]) -> bool:
        """
        Validate price/currency amount
        Accepts strings, floats, or integers
        """
        try:
            price_float = float(price)
            return price_float >= 0 and round(price_float, 2) == price_float
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_quantity(quantity: Union[str, int]) -> bool:
        """
        Validate inventory quantity (must be positive integer)
        """
        try:
            qty = int(quantity)
            return qty >= 0
        except (ValueError, TypeError):
            return False
        
    @staticmethod
    def validate_serial_number(serial: str, min_length: int = 4, max_length: int = 20) -> bool:
        """
        Validate product serial numbers.
        Typical serial numbers contain alphanumeric characters and certain symbols.
        """
        if not serial:
            return False
            
        serial = serial.strip()
        
        # Basic checks
        if not (min_length <= len(serial) <= max_length):
            return False
            
        # Common serial number patterns:
        # - Alphanumeric with possible hyphens, underscores, or dots
        # - No consecutive special characters
        # - Starts and ends with alphanumeric
        pattern = r'^[a-zA-Z0-9]+([-_\.][a-zA-Z0-9]+)*$'
        return bool(re.match(pattern, serial))

    @staticmethod
    def validate_imei(imei: str) -> bool:
        """
        Validate IMEI (International Mobile Equipment Identity) numbers.
        IMEIs are 15-digit numbers that include a check digit (Luhn algorithm).
        """
        if not imei:
            return False
            
        # Remove any non-digit characters
        imei_digits = ''.join(c for c in imei if c.isdigit())
        
        # Check length (standard IMEI is 15 digits, IMEISV is 16 digits)
        if len(imei_digits) not in (15, 16):
            return False
            
        # For 15-digit IMEI, validate check digit using Luhn algorithm
        if len(imei_digits) == 15:
            total = 0
            for i, digit in enumerate(imei_digits[:14]):
                num = int(digit)
                if i % 2 == 1:  # Double every other digit (0-indexed, so odd positions)
                    num *= 2
                    if num > 9:
                        num = (num // 10) + (num % 10)
                total += num
                
            check_digit = (10 - (total % 10)) % 10
            return check_digit == int(imei_digits[14])
            
        return True  # 16-digit IMEISV doesn't have check digit
    
    @staticmethod
    def format_serial_number(serial: str) -> str:
        """
        Format serial number by:
        - Converting to uppercase
        - Removing invalid characters (keeps alphanumeric, hyphen, underscore)
        """
        if not serial:
            return serial
            
        # Remove any non-alphanumeric characters except hyphens and underscores
        cleaned = re.sub(r'[^a-zA-Z0-9-_]', '', serial)
        # Convert to uppercase
        return cleaned.upper()

    @staticmethod
    def format_imei(imei: str) -> str:
        """
        Format IMEI number by:
        - Removing all non-digit characters
        - Adding spaces every 4 digits
        - Limiting to 16 digits max
        """
        if not imei:
            return imei
            
        # Remove all non-digit characters
        digits = re.sub(r'[^\d]', '', imei)
        # Limit to 16 digits
        digits = digits[:16]
        
        # Format with spaces every 4 digits
        formatted = []
        for i in range(0, len(digits), 4):
            formatted.append(digits[i:i+4])
        return ' '.join(formatted)

    @staticmethod
    def get_imei_style_sheet(imei: str) -> str:
        """
        Get Qt stylesheet for IMEI input based on validity
        Returns stylesheet string for valid/invalid state
        """
        digits = re.sub(r'[^\d]', '', imei) if imei else ''
        is_valid = len(digits) in (15, 16) and all(c.isdigit() for c in digits)
        
        return (
            f"background-color: {'#f8fff8' if is_valid else '#fff8f8'};"
            f"border: 1px solid {'#a0a0a0' if is_valid else '#ff0000'};"
        )

    @staticmethod
    def password_has_uppercase(password: str) -> bool:
        """Check if password contains at least one uppercase letter."""
        return any(c.isupper() for c in password)

    @staticmethod
    def password_has_lowercase(password: str) -> bool:
        """Check if password contains at least one lowercase letter."""
        return any(c.islower() for c in password)

    @staticmethod
    def password_has_number(password: str) -> bool:
        """Check if password contains at least one number."""
        return any(c.isdigit() for c in password)

    @staticmethod
    def password_has_special_char(password: str) -> bool:
        """Check if password contains at least one special character."""
        return any(not c.isalnum() for c in password)

    @staticmethod
    def password_meets_length(password: str, min_length: int = 8) -> bool:
        """Check if password meets minimum length requirement."""
        return len(password) >= min_length

    @staticmethod
    def get_password_requirement_stylesheet(password: str) -> dict:
        """
        Get stylesheet information for password requirements.
        Returns a dictionary with requirement names as keys and style information as values.
        """
        return {
            'length': {
                'valid': InputValidator.password_meets_length(password),
                'message': f"Minimum {InputValidator.MIN_PASSWORD_LENGTH} characters",
                'style': "color: green;" if InputValidator.password_meets_length(password) else "color: red;"
            },
            'uppercase': {
                'valid': InputValidator.password_has_uppercase(password),
                'message': "1 uppercase letter",
                'style': "color: green;" if InputValidator.password_has_uppercase(password) else "color: red;"
            },
            'lowercase': {
                'valid': InputValidator.password_has_lowercase(password),
                'message': "1 lowercase letter",
                'style': "color: green;" if InputValidator.password_has_lowercase(password) else "color: red;"
            },
            'number': {
                'valid': InputValidator.password_has_number(password),
                'message': "1 number",
                'style': "color: green;" if InputValidator.password_has_number(password) else "color: red;"
            },
            'special': {
                'valid': InputValidator.password_has_special_char(password),
                'message': "1 special character",
                'style': "color: green;" if InputValidator.password_has_special_char(password) else "color: red;"
            }
        }

    @staticmethod
    def get_password_match_stylesheet(password: str, confirm_password: str) -> str:
        """
        Get stylesheet for password match indicator.
        Returns green style if passwords match and aren't empty, red otherwise.
        """
        if password and confirm_password and password == confirm_password:
            return "color: green; font-weight: bold;"
        elif password and confirm_password:
            return "color: red; font-weight: bold;"
        return ""