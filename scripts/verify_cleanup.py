#!/usr/bin/env python3
"""
Test script to verify About dialog and code cleanup.
"""

import sys
import os

# Add src/app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'app'))

print("🧪 Testing Code Cleanup and About Dialog...")
print()

# Test 1: Verify legacy files are removed
print("1️⃣ Checking legacy files removed...")
legacy_files = [
    'src/app/views/tickets/tickets.py',
    'src/app/views/device/devices.py',
    'src/app/views/inventory/parts_list_tab.py',
    'src/app/views/inventory/supplier_list_tab.py',
    'src/app/views/inventory/category_list_tab.py',
]

all_removed = True
for file_path in legacy_files:
    if os.path.exists(file_path):
        print(f"   ❌ {file_path} still exists")
        all_removed = False
    else:
        print(f"   ✅ {file_path} removed")

if all_removed:
    print("   ✅ All legacy files removed successfully!")
else:
    print("   ⚠️  Some legacy files still exist")

print()

# Test 2: Verify About dialog can be imported
print("2️⃣ Testing About dialog import...")
try:
    from views.dialogs.about_dialog import AboutDialog, show_about_dialog
    print("   ✅ About dialog imports successfully")
except ImportError as e:
    print(f"   ❌ Failed to import About dialog: {e}")
    sys.exit(1)

print()

# Test 3: Verify version module exists
print("3️⃣ Testing version module...")
try:
    from version import VERSION, FULL_VERSION, BUILD_NUMBER
    print(f"   ✅ Version: {VERSION}")
    print(f"   ✅ Full Version: {FULL_VERSION}")
    print(f"   ✅ Build Number: {BUILD_NUMBER}")
except ImportError:
    print("   ⚠️  Version module not found (run generate_version.py first)")

print()

# Test 4: Verify modern tabs still exist
print("4️⃣ Checking modern tabs exist...")
modern_tabs = [
    ('ModernTicketsTab', 'views.tickets.modern_tickets_tab'),
    ('ModernDevicesTab', 'views.device.modern_devices_tab'),
    ('ModernPartsListTab', 'views.inventory.modern_parts_list_tab'),
    ('ModernSupplierListTab', 'views.inventory.modern_supplier_list_tab'),
    ('ModernCategoryListTab', 'views.inventory.modern_category_list_tab'),
]

all_exist = True
for tab_name, module_path in modern_tabs:
    try:
        module = __import__(module_path, fromlist=[tab_name])
        getattr(module, tab_name)
        print(f"   ✅ {tab_name} exists")
    except (ImportError, AttributeError) as e:
        print(f"   ❌ {tab_name} not found: {e}")
        all_exist = False

if all_exist:
    print("   ✅ All modern tabs exist!")

print()
print("=" * 50)
print("✅ Code cleanup and About dialog verification complete!")
print("=" * 50)
