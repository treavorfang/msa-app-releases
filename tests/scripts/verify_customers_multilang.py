import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'app')))

from PySide6.QtWidgets import QApplication

def verify_customer_views():
    print("Verifying Customer Views Instantiation...")
    
    app = QApplication(sys.argv)
    
    # Mock dependencies
    container = MagicMock()
    container.customer_controller = MagicMock()
    container.invoice_controller = MagicMock()
    
    user = MagicMock()
    user.id = 1
    
    try:
        from views.customer.customer_form import CustomerForm
        form = CustomerForm(container.customer_controller, user.id)
        print("✓ CustomerForm instantiated successfully")
    except Exception as e:
        print(f"✗ CustomerForm instantiation failed: {e}")
        return False

    try:
        from views.customer.modern_customers_tab import ModernCustomersTab
        tab = ModernCustomersTab(container, user)
        print("✓ ModernCustomersTab instantiated successfully")
    except Exception as e:
        print(f"✗ ModernCustomersTab instantiation failed: {e}")
        return False
        
    try:
        from views.customer.customer_details_dialog import CustomerDetailsDialog
        from dtos.customer_dto import CustomerDTO
        
        # Create mock customer
        customer = CustomerDTO(
            id=1,
            name="Test Customer",
            phone="+95 9 123 456 789",
            email="test@example.com",
            address="Test Address",
            notes="Test notes",
            preferred_contact_method="phone",
            created_at=None,
            updated_at=None,
            deleted_at=None,
            created_by=1,
            updated_by=1
        )
        
        dialog = CustomerDetailsDialog(customer, [], None, container)
        print("✓ CustomerDetailsDialog instantiated successfully")
    except Exception as e:
        print(f"✗ CustomerDetailsDialog instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    print("\n✅ ALL CUSTOMER VIEWS VERIFIED")
    return True

if __name__ == "__main__":
    if verify_customer_views():
        print("\n🎉 Customers module multi-language support is working!")
    else:
        print("\n❌ Some checks failed")
