"""
Core license generation logic
"""
import os
import json
import base64
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from .config import PRIVATE_KEY_PATH, LIFETIME_EXPIRY


class LicenseGeneratorCore:
    """Handles license key generation"""
    
    def __init__(self):
        self.private_key = None
        self._load_private_key()
    
    def _load_private_key(self):
        """Load the private key from file"""
        if not os.path.exists(PRIVATE_KEY_PATH):
            raise FileNotFoundError(f"Private key not found at: {PRIVATE_KEY_PATH}")
        
        with open(PRIVATE_KEY_PATH, "rb") as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(), password=None
            )
    
    def is_key_loaded(self):
        """Check if private key is loaded"""
        return self.private_key is not None and os.path.exists(PRIVATE_KEY_PATH)
    
    def generate(self, customer_name: str, hwid: str, duration_days: int) -> dict:
        """
        Generate a license key
        
        Args:
            customer_name: Name of the customer
            hwid: Hardware ID
            duration_days: License duration in days (-1 for lifetime)
        
        Returns:
            dict with 'license_key', 'expiry_date', 'customer_name', 'hwid'
        
        Raises:
            ValueError: If validation fails
            RuntimeError: If key generation fails
        """
        # Validate inputs
        if not customer_name or not customer_name.strip():
            raise ValueError("Customer name is required")
        
        if not hwid or not hwid.strip():
            raise ValueError("Hardware ID is required")
        
        if not self.private_key:
            raise RuntimeError("Private key not loaded")
        
        # Calculate expiry date
        if duration_days == -1:  # Lifetime
            expiry_date = LIFETIME_EXPIRY
        else:
            expiry = datetime.now() + timedelta(days=duration_days)
            expiry_date = expiry.strftime("%Y-%m-%d")
        
        try:
            # Create payload
            payload = {
                "hwid": hwid.strip(),
                "expiry": expiry_date,
                "name": customer_name.strip(),
                "generated_at": datetime.now().isoformat()
            }
            
            payload_json = json.dumps(payload).encode()
            payload_b64 = base64.urlsafe_b64encode(payload_json)
            
            # Sign
            signature = self.private_key.sign(payload_b64)
            sig_b64 = base64.urlsafe_b64encode(signature)
            
            # Combine
            license_key = payload_b64 + b"." + sig_b64
            final_key = license_key.decode()
            
            return {
                "license_key": final_key,
                "expiry_date": expiry_date,
                "customer_name": customer_name.strip(),
                "hwid": hwid.strip(),
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate license: {str(e)}")
