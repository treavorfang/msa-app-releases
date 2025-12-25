import hashlib
from datetime import datetime
import socket
import psutil

def generate_daily_pin():
    """
    Generate a deterministic 4-digit PIN based on the current date.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    hash_object = hashlib.sha256(today.encode())
    pin_int = int(hash_object.hexdigest(), 16)
    return f"{pin_int % 10000:04d}"

def get_local_ip():
    """
    Get the primary local IP address.
    Prioritizes active physical interfaces using psutil, with a robust socket fallback.
    """
    # Method 1: Use psutil to find an active IPv4 address on a physical interface
    try:
        # Sort interfaces to prefer those that look like standard LAN/WLAN
        interfaces = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        # Priority patterns for interface names
        priority_prefixes = ('en', 'eth', 'wlan', 'bridge')
        
        selected_ips = []
        
        for iface, addrs in interfaces.items():
            # Skip interfaces that are down or are loopback
            if iface in stats and not stats[iface].isup:
                continue
            if iface.startswith('lo'):
                continue
                
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ip = addr.address
                    # Skip loopback and link-local
                    if ip.startswith("127.") or ip.startswith("169.254"):
                        continue
                    
                    # Store with priority if it matches common naming conventions
                    priority = 0
                    if any(iface.lower().startswith(p) for p in priority_prefixes):
                        priority = 1
                    
                    selected_ips.append((priority, ip))
        
        if selected_ips:
            # Sort by priority (descending) and return the first one
            selected_ips.sort(key=lambda x: x[0], reverse=True)
            return selected_ips[0][1]
            
    except Exception:
        pass

    # Method 2: Improved socket fallback (the "UDP trick")
    # This doesn't actually send data, but forces the OS to choose an interface
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Use a reachable IP to force a routing table lookup
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not (ip.startswith("127.") or ip.startswith("169.254")):
            return ip
    except Exception:
        pass
    
    return "127.0.0.1"

def get_pairing_url(port):
    """Generate the URL for the mobile app to connect to."""
    ip = get_local_ip()
    return f"http://{ip}:{port}/static/index.html"
