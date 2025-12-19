import os
import sys
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
import base64

def verify_keys():
    """Verify that private and public keys exist and form a valid pair."""
    SCRIPT_DIR = Path(__file__).parent
    PROJECT_ROOT = SCRIPT_DIR.parent
    
    # Paths
    PRIVATE_KEY_PATH = PROJECT_ROOT / "private.pem"
    PUBLIC_KEY_PATH = PROJECT_ROOT / "src" / "app" / "config" / "public.pem"
    
    print(f"Checking keys...")
    print(f"Private Key: {PRIVATE_KEY_PATH}")
    print(f"Public Key:  {PUBLIC_KEY_PATH}")
    
    if not PRIVATE_KEY_PATH.exists():
        print("❌ Error: private.pem not found.")
        return False
        
    if not PUBLIC_KEY_PATH.exists():
        print("❌ Error: public.pem not found.")
        return False
        
    try:
        # Load Private Key
        with open(PRIVATE_KEY_PATH, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
            
        # Load Public Key
        with open(PUBLIC_KEY_PATH, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())
            
        # Verify Pair by signing and verifying data
        data = b"test_verification_data"
        signature = private_key.sign(data)
        
        try:
            public_key.verify(signature, data)
            print("✅ Keys matched! Signature verification successful.")
            return True
        except Exception as e:
            print("❌ Error: Keys do not match. Public key cannot verify private key signature.")
            return False
            
    except Exception as e:
        print(f"❌ Error loading keys: {e}")
        return False

if __name__ == "__main__":
    if verify_keys():
        sys.exit(0)
    else:
        sys.exit(1)
