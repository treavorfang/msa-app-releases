
import sys
import os
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add src/app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'app')))

from PySide6.QtWidgets import QApplication
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

# Mock dependencies
sys.modules['utils.print.invoice_generator'] = MagicMock()

# Mock container and controllers
mock_container = MagicMock()
mock_container.business_settings_service = MagicMock()
mock_container.invoice_controller = MagicMock()
mock_container.payment_controller = MagicMock()
mock_container.device_controller = MagicMock()
mock_container.ticket_controller = MagicMock()
mock_container.inventory_controller = MagicMock()
mock_container.repair_part_controller = MagicMock()

# Mock objects
mock_ticket = MagicMock()
mock_ticket.ticket_number = "T-123"
mock_ticket.customer.name = "Test Customer"
mock_ticket.device.brand = "Test Brand"
mock_ticket.device.model = "Test Model"

mock_invoice = MagicMock()
mock_invoice.invoice_number = "INV-2023-001"
mock_invoice.created_at = datetime.now()
mock_invoice.due_date = datetime.now()
mock_invoice.payment_status = "unpaid"
mock_invoice.subtotal = 100.0
mock_invoice.tax = 10.0
mock_invoice.discount = 5.0
mock_invoice.total = 105.0
mock_invoice.items = []
mock_invoice.payments = []
mock_invoice.error_description = "Test Issue"

mock_user = MagicMock()

def verify_invoice_multilang():
    print("Verifying Invoice Multi-Language Support...")
    
    app = QApplication(sys.argv)
    
    # 1. Test LanguageManager loading
    print("\n1. Testing LanguageManager...")
    lm = language_manager
    print(f"Current Language: {lm.current_language}")
    
    invoice_title = lm.get("Invoices.invoices", "Invoices")
    print(f"Invoices Title: {invoice_title}")
    
    if invoice_title == "Invoices":
        print("✅ LanguageManager loaded successfully")
    else:
        print("❌ LanguageManager failed to load expected string")

    # 2. Test CurrencyFormatter
    print("\n2. Testing CurrencyFormatter...")
    formatted_price = currency_formatter.format(1234.56)
    print(f"Formatted Price: {formatted_price}")
    if "$" in formatted_price:
        print("✅ CurrencyFormatter working")
    else:
        print("❌ CurrencyFormatter failed")

    # 3. Test View Instantiation
    print("\n3. Testing View Instantiation...")
    
    try:
        from views.invoice.modern_invoice_tab import ModernInvoiceTab
        from views.invoice.create_customer_invoice_dialog import CreateCustomerInvoiceDialog
        from views.invoice.customer_invoice_details_dialog import CustomerInvoiceDetailsDialog
        from views.invoice.record_customer_payment_dialog import RecordCustomerPaymentDialog
        
        # ModernInvoiceTab
        print("Instantiating ModernInvoiceTab...")
        tab = ModernInvoiceTab(mock_container, mock_user)
        print("✅ ModernInvoiceTab instantiated")
        
        # CreateCustomerInvoiceDialog
        print("Instantiating CreateCustomerInvoiceDialog...")
        create_dialog = CreateCustomerInvoiceDialog(mock_container, mock_ticket, mock_user)
        print("✅ CreateCustomerInvoiceDialog instantiated")
        
        # CustomerInvoiceDetailsDialog
        print("Instantiating CustomerInvoiceDetailsDialog...")
        # Mock get_invoice return
        mock_container.invoice_controller.get_invoice.return_value = mock_invoice
        details_dialog = CustomerInvoiceDetailsDialog(mock_container, 1, mock_user)
        print("✅ CustomerInvoiceDetailsDialog instantiated")
        
        # RecordCustomerPaymentDialog
        print("Instantiating RecordCustomerPaymentDialog...")
        payment_dialog = RecordCustomerPaymentDialog(mock_container, mock_invoice, mock_user)
        print("✅ RecordCustomerPaymentDialog instantiated")
        
    except Exception as e:
        print(f"❌ Failed to instantiate views: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_invoice_multilang()
