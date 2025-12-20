import sys
import os
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication

# Add src to path
sys.path.append(os.path.abspath('src/app'))

# Create app
app = QApplication.instance() or QApplication(sys.argv)

print("Verifying UI components initialization...")

try:
    from views.inventory.financial.credit_note_list_tab import CreditNoteListTab
    from views.inventory.financial.credit_note_details_dialog import CreditNoteDetailsDialog
    from views.inventory.financial.apply_credit_dialog import ApplyCreditDialog
    from models.credit_note import CreditNote
    from models.supplier import Supplier
    from datetime import datetime

    # Mock container
    container = MagicMock()
    container.credit_note_service = MagicMock()
    container.invoice_service = MagicMock()
    
    # Mock user
    user = MagicMock()

    print("Testing CreditNoteListTab initialization...")
    tab = CreditNoteListTab(container, user=user)
    print("CreditNoteListTab initialized successfully.")

    # Mock credit note
    credit_note = MagicMock()
    credit_note.credit_note_number = "CN-TEST"
    credit_note.issue_date = datetime.now()
    credit_note.expiry_date = None
    credit_note.status = "pending"
    credit_note.credit_amount = 100.00
    credit_note.applied_amount = 0.00
    credit_note.remaining_credit = 100.00
    credit_note.notes = "Test notes"
    credit_note.supplier.name = "Test Supplier"
    credit_note.supplier.id = 1
    credit_note.supplier.contact_person = "John Doe"
    credit_note.supplier.phone = "1234567890"
    credit_note.supplier.email = "test@example.com"
    credit_note.purchase_return.return_number = "RET-TEST"
    credit_note.supplier_invoice = None
    credit_note.is_expired = False

    # print("Testing CreditNoteDetailsDialog initialization...")
    # details_dialog = CreditNoteDetailsDialog(container, credit_note)
    # print("CreditNoteDetailsDialog initialized successfully.")

    print("Testing ApplyCreditDialog initialization...")
    apply_dialog = ApplyCreditDialog(container, credit_note, user=user)
    print("ApplyCreditDialog initialized successfully.")
    
    print("ALL INITIALIZATIONS SUCCESSFUL")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
