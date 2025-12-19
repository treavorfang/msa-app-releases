
import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'app')))

from views.tickets.ticket_receipt_actions import TicketReceiptActions
from PySide6.QtWidgets import QApplication

def verify_legacy_mapping():
    app = QApplication(sys.argv)
    
    # Mock TicketReceipt and its sections
    mock_receipt = MagicMock()
    mock_receipt.business_settings_service = None
    
    # Mock Customer Section
    mock_receipt.customer_section.get_customer_data.return_value = {
        'name': 'Test Customer',
        'phone': '1234567890',
        'email': 'test@example.com',
        'address': '123 Test St',
        'customer_id': 1
    }
    mock_receipt.customer_section.customer_name.text.return_value = 'Test Customer'
    mock_receipt.customer_section.customer_phone.text.return_value = '1234567890'
    mock_receipt.customer_section.customer_address.text.return_value = '123 Test St'
    
    # Mock Device Section
    mock_receipt.device_section.get_device_data.return_value = {
        'brand': 'Test Brand',
        'model': 'Test Model',
        'imei': '123456789012345',
        'serial_number': 'SN123456',
        'color': 'Black',
        'condition': 'Good'
    }
    
    # Mock Issue Section
    mock_receipt.issue_section.get_issue_data.return_value = {
        'error': 'Broken Screen',
        'error_description': 'Screen is cracked'
    }
    
    # Mock Controls Section
    mock_receipt.controls_section.get_controls_data.return_value = {
        'priority': 'high',
        'deadline': '2025-12-07',
        'estimated_cost': 100.0,
        'deposit_paid': 0.0
    }
    mock_receipt.controls_section.technician_input.currentData.return_value = None
    
    # Initialize Actions
    actions = TicketReceiptActions(mock_receipt)
    
    # Gather Data
    data = actions._gather_ticket_data_for_print()
    
    # Verify Serial Number
    if 'serial_number' in data and data['serial_number'] == 'SN123456':
        print("SUCCESS: Serial Number is correctly mapped in TicketReceiptActions.")
    else:
        print(f"FAILURE: Serial Number is missing or incorrect. Data keys: {data.keys()}")
        if 'serial_number' in data:
            print(f"Value: {data['serial_number']}")

if __name__ == "__main__":
    verify_legacy_mapping()
