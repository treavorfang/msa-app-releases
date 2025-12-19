import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'app')))

from PySide6.QtWidgets import QApplication
from utils.language_manager import language_manager

def verify_language_manager():
    print("Verifying Language Manager...")
    
    # Test loading English
    if not language_manager.load_language("English"):
        print("FAILURE: Failed to load English language")
        return False
        
    # Test getting a key
    new_ticket_label = language_manager.get("Tickets.new_ticket")
    print(f"Tickets.new_ticket: {new_ticket_label}")
    
    if new_ticket_label == "Tickets.new_ticket":
        print("FAILURE: Failed to retrieve translation for Tickets.new_ticket")
        return False
        
    print("SUCCESS: Language Manager verified.")
    return True

def verify_ticket_views():
    print("\nVerifying Ticket Views Instantiation...")
    
    app = QApplication(sys.argv)
    
    # Mock dependencies
    container = MagicMock()
    container.ticket_service = MagicMock()
    container.device_service = MagicMock()
    container.customer_service = MagicMock()
    container.technician_service = MagicMock()
    container.business_settings_service = MagicMock()
    container.ticket_controller = MagicMock()
    container.technician_controller = MagicMock()
    
    user = MagicMock()
    user.id = 1
    
    try:
        from views.tickets.modern_ticket_receipt import ModernTicketReceiptDialog
        dialog = ModernTicketReceiptDialog(container, user)
        print("SUCCESS: ModernTicketReceiptDialog instantiated.")
    except Exception as e:
        print(f"FAILURE: ModernTicketReceiptDialog instantiation failed: {e}")
        return False

    try:
        from views.tickets.modern_tickets_tab import ModernTicketsTab
        tab = ModernTicketsTab(container, user)
        print("SUCCESS: ModernTicketsTab instantiated.")
    except Exception as e:
        print(f"FAILURE: ModernTicketsTab instantiation failed: {e}")
        return False
        
    return True

if __name__ == "__main__":
    if verify_language_manager() and verify_ticket_views():
        print("\nALL CHECKS PASSED")
    else:
        print("\nSOME CHECKS FAILED")
