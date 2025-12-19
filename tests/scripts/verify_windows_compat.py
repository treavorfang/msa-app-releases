
import os
import sys
import platform
import subprocess
import importlib.util

def check_windows_compatibility():
    print(f"🖥️  OS: {platform.system()} {platform.release()}")
    print("🔍 Checking Windows Compatibility...")
    
    issues = []
    
    # 1. Check Module Dependencies
    print("\n📦 Checking Dependencies...")
    required_modules = ['psutil', 'peewee', 'PySide6', 'weasyprint', 'barcode', 'qrcode']
    for mod in required_modules:
        if importlib.util.find_spec(mod) is None:
            if mod == 'psutil': # Optional on Mac/Linux but required for full features on Windows
                 print(f"⚠️  {mod} not found (Recommended for System Monitor on Windows)")
            else:
                 print(f"❌ {mod} not found!")
                 issues.append(f"Missing dependency: {mod}")
        else:
            print(f"✅ {mod} installed")

    # 2. Check File Paths
    print("\n📂 Checking File Paths...")
    # Verify we aren't using forward slashes hardcoded in critical paths
    # This is a heuristic check
    from config.config import DATABASE_PATH, ICON_DIR
    print(f"   Database Path: {DATABASE_PATH}")
    print(f"   Icon Dir: {ICON_DIR}")
    
    if '/' in str(DATABASE_PATH) and '\\' not in str(DATABASE_PATH) and os.name == 'nt':
         # Python handles mixed slashes well usually, but worth noting
         print("⚠️  Warning: Paths might be using forward slashes on Windows.")
    else:
         print("✅ Path separators look okay for this OS.")

    # 3. Check System Monitor Service Fallback
    print("\n🔌 Checking System Monitor Service...")
    sys.path.append(os.path.join(os.getcwd(), '..', '..', 'src', 'app'))
    try:
        from services.system_monitor_service import SystemMonitorService
        monitor = SystemMonitorService()
        mem = monitor._get_memory_usage()
        print(f"   Memory Usage Check: {mem}")
        if mem['status'] == 'Unknown' and platform.system() == 'Windows':
             issues.append("System Monitor failed to get memory usage (install psutil)")
        else:
             print("✅ System Monitor compatible")
    except Exception as e:
        print(f"❌ System Monitor Error: {e}")
        issues.append(f"System Monitor Error: {e}")

    # 4. Check PDF Preview Logic
    print("\n📄 Checking PDF Preview Logic...")
    from utils.print.invoice_generator import InvoiceGenerator
    # We won't actually generate a PDF to avoid GUI requirement, but we check imports
    print("✅ InvoiceGenerator imported successfully")

    # 5. Summary
    print("\n" + "="*30)
    if issues:
        print(f"❌ Found {len(issues)} potential issues for Windows:")
        for i in issues:
            print(f" - {i}")
        sys.exit(1)
    else:
        print("✅ No critical Windows compatibility issues found!")
        print("   Note: Ensure 'psutil' is installed on Windows for full monitoring.")
        print("   Note: PDF Burmese font support requires custom font registration (general issue).")
        sys.exit(0)

if __name__ == "__main__":
    check_windows_compatibility()
