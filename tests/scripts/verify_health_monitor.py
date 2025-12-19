
from services.system_monitor_service import SystemMonitorService
from config.database import initialize_database, db

def verify_system_monitor():
    print("🚀 Starting System Monitor Service Verification...")
    
    # Init DB
    if db.is_closed():
        # Using in-memory or existing test db
        initialize_database()
        
    monitor = SystemMonitorService()
    stats = monitor.get_system_stats()
    
    # Verify basic keys
    expected_keys = ["uptime", "memory", "disk", "system", "database"]
    for key in expected_keys:
        assert key in stats, f"Missing key: {key}"
        print(f"✅ Found key: {key}")
        
    # Check values sanity
    print("\n--- Uptime ---")
    print(stats['uptime']['formatted'])
    assert stats['uptime']['days'] >= 0
    
    print("\n--- Memory ---")
    print(f"{stats['memory']['used_mb']} MB")
    assert stats['memory']['used_mb'] > 0
    
    print("\n--- Disk ---")
    print(f"{stats['disk']['percent']}% used")
    assert stats['disk']['total_gb'] > 0
    
    print("\n--- DB ---")
    print(f"Latency: {stats['database']['latency_ms']} ms")
    assert stats['database']['status'] in ["Connected", "Error"]
    
    print("\n✨ System Monitor Verification PASSED!")

if __name__ == "__main__":
    verify_system_monitor()
