import sys
import os

# Add src to path
sys.path.append(os.path.abspath('src/app'))

print("Verifying imports...")

try:
    print("Importing constants...")
    from config.constants import UIColors, CreditNoteStatus, InvoiceStatus
    print("Constants imported successfully.")

    print("Importing CreditNoteListTab...")
    from views.inventory.financial.credit_note_list_tab import CreditNoteListTab
    print("CreditNoteListTab imported successfully.")

    print("Importing CreditNoteDetailsDialog...")
    from views.inventory.financial.credit_note_details_dialog import CreditNoteDetailsDialog
    print("CreditNoteDetailsDialog imported successfully.")

    print("Importing ApplyCreditDialog...")
    from views.inventory.financial.apply_credit_dialog import ApplyCreditDialog
    print("ApplyCreditDialog imported successfully.")

    print("Importing ModernFinancialTab...")
    from views.financial.modern_financial_tab import ModernFinancialTab
    print("ModernFinancialTab imported successfully.")
    
    print("ALL IMPORTS SUCCESSFUL")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
