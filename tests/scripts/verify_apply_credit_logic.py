import sys
import os
from unittest.mock import MagicMock
from decimal import Decimal

# Add src to path
sys.path.append(os.path.abspath('src/app'))

try:
    from core.dependency_container import DependencyContainer
    from views.inventory.financial.apply_credit_dialog import ApplyCreditDialog
    from models.credit_note import CreditNote
    from models.supplier_invoice import SupplierInvoice
    
    print("Initializing DependencyContainer...")
    container = DependencyContainer()
    
    print("Getting services...")
    credit_note_service = container.credit_note_service
    supplier_invoice_service = container.supplier_invoice_service
    
    # Mock data
    print("Setting up mock data...")
    user = MagicMock()
    user.id = 1
    user.username = "test_user"
    
    # Create a real credit note if possible, or mock it
    # Ideally we use real DB objects to test the service logic
    # But for now let's try to list existing ones
    credit_notes = credit_note_service.list_credit_notes()
    if not credit_notes:
        print("No credit notes found. Cannot test with real data.")
        # Create a mock credit note
        credit_note = MagicMock()
        credit_note.id = 999
        credit_note.credit_note_number = "CN-TEST"
        credit_note.remaining_credit = 100.00
        credit_note.supplier.id = 1
        credit_note.supplier.name = "Test Supplier"
    else:
        credit_note = credit_notes[0]
        print(f"Using Credit Note: {credit_note.credit_note_number} (ID: {credit_note.id})")
        
    # Initialize Dialog (headless)
    print("Initializing ApplyCreditDialog...")
    # We mock QDialog methods to avoid GUI issues
    ApplyCreditDialog.exec = MagicMock(return_value=True)
    ApplyCreditDialog.accept = MagicMock()
    ApplyCreditDialog.reject = MagicMock()
    ApplyCreditDialog.setWindowTitle = MagicMock()
    ApplyCreditDialog.setMinimumSize = MagicMock()
    
    # We need a QApplication for widgets
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    
    dialog = ApplyCreditDialog(container, credit_note, user=user)
    
    # Test _load_invoices
    print("Testing _load_invoices...")
    dialog._load_invoices()
    count = dialog.invoice_combo.count()
    print(f"Loaded {count} items in combo box.")
    
    if count > 1:
        # Select the first invoice (index 1, index 0 is "Select Invoice...")
        dialog.invoice_combo.setCurrentIndex(1)
        invoice = dialog.invoice_combo.currentData()
        print(f"Selected Invoice: {invoice.invoice_number} (ID: {invoice.id})")
        
        # Test _on_apply
        print("Testing _on_apply...")
        dialog.amount_spin.setValue(10.00)
        
        # Mock message boxes
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning = MagicMock()
        QMessageBox.information = MagicMock()
        QMessageBox.critical = MagicMock()
        
        dialog._on_apply()
        
        # Check if success message was shown
        if QMessageBox.information.called:
            print("SUCCESS: Credit applied successfully.")
        elif QMessageBox.warning.called:
            print("FAILURE: Warning shown.")
            print(QMessageBox.warning.call_args)
        elif QMessageBox.critical.called:
            print("FAILURE: Critical error shown.")
            print(QMessageBox.critical.call_args)
        else:
            print("FAILURE: No message shown.")
            
    else:
        print("No invoices found to apply credit to.")

    print("VERIFICATION COMPLETE")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
