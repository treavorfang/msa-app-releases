# src/app/utils/security/password_utils.py
import hashlib
import binascii
import os
from config.config_manager import PASSWORD_HASH_METHOD, PASSWORD_SALT_LENGTH

def hash_password(password: str) -> str:
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')[:PASSWORD_SALT_LENGTH]
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a stored password against one provided by user"""
    salt = stored_password[:PASSWORD_SALT_LENGTH]
    stored_password = stored_password[PASSWORD_SALT_LENGTH:]
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt.encode('ascii'), 100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password