import sys
import json
import base64
import argparse
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

def create_license(hwid, expiry, name):
    """Create a signed license string."""
    try:
        # Load Private Key
        with open("private.pem", "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(), password=None
            )
    except FileNotFoundError:
        print("❌ Error: private.pem not found. Run generate_keys.py first.")
        return

    # Payload
    payload = {
        "hwid": hwid,
        "expiry": expiry, # YYYY-MM-DD
        "name": name
    }
    payload_json = json.dumps(payload).encode()
    payload_b64 = base64.urlsafe_b64encode(payload_json)

    # Sign Payload
    signature = private_key.sign(payload_b64)
    sig_b64 = base64.urlsafe_b64encode(signature)

    # Final License Key
    license_key = payload_b64 + b"." + sig_b64
    print(f"\n🔑 LICENCE KEY FOR {name}:")
    print("-" * 60)
    print(license_key.decode())
    print("-" * 60)
    print(f"HWID: {hwid}")
    print(f"Expiry: {expiry}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python create_license.py <HWID> <EXPIRY_YYYY-MM-DD> <CUSTOMER_NAME>")
        print("Example: python create_license.py 982A73B6201C2025 2026-01-01 'John Doe'")
    else:
        create_license(sys.argv[1], sys.argv[2], sys.argv[3])
