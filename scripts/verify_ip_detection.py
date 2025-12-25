import sys
import os

# Add src/app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'app')))

from utils.mobile_utils import get_local_ip

def verify():
    print("Testing improved get_local_ip()...")
    ip = get_local_ip()
    print(f"Detected Local IP: {ip}")
    
    if ip == "127.0.0.1":
        print("WARNING: Only loopback detected. This might be expected if not connected to a network.")
    elif ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
        print("SUCCESS: Valid LAN IP detected.")
    else:
        print(f"INFO: Detected IP {ip} is not in a standard private range, but might be valid.")

if __name__ == "__main__":
    verify()
