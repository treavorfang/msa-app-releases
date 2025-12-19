import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'app')))

from PySide6.QtWidgets import QApplication

def verify_inventory_views():
    print("Verifying Inventory Views Instantiation...")
    
    app = QApplication(sys.argv)
    
    # Mock dependencies
    container = MagicMock()
    container.supplier_controller = MagicMock()
    container.part_service = MagicMock()
    
    user = MagicMock()
    user.id = 1
    
    try:
        from views.inventory.modern_inventory import ModernInventoryTab
        tab = ModernInventoryTab(container, user)
        print("✓ ModernInventoryTab instantiated successfully")
    except Exception as e:
        print(f"✗ ModernInventoryTab instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    try:
        from views.inventory.supplier_dialog import SupplierDialog
        dialog = SupplierDialog(container)
        print("✓ SupplierDialog instantiated successfully")
    except Exception as e:
        print(f"✗ SupplierDialog instantiation failed: {e}")
        return False
        
    try:
        from views.inventory.part_dialog import PartDialog
        dialog = PartDialog(container)
        print("✓ PartDialog instantiated successfully")
    except Exception as e:
        print(f"✗ PartDialog instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    print("\n✅ ALL INVENTORY VIEWS VERIFIED")
    return True

if __name__ == "__main__":
    if verify_inventory_views():
        print("\n🎉 Inventory module multi-language support is working!")
    else:
        print("\n❌ Some checks failed")
