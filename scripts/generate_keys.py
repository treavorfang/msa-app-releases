import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

def generate_keys():
    """Generate Ed25519 public/private keypair."""
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Save Private Key (KEEP SECURE!)
    with open("private.pem", "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # Save Public Key (Ship with App)
    with open("public.pem", "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

    print("✅ Keys generated:")
    print("   private.pem (KEEP SECRET - Used to sign licenses)")
    print("   public.pem  (SHIP WITH APP - verifies licenses)")

if __name__ == "__main__":
    generate_keys()
