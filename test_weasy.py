
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))
sys.path.append(os.path.join(os.getcwd(), 'src', 'app'))

from unittest.mock import MagicMock
from app.utils.print.ticket_generator import TicketReceiptGenerator

# Mock service
mock_settings = MagicMock()
mock_settings.get_settings.return_value = MagicMock(
    business_name="Test Shop",
    address="123 Test St",
    business_phone="555-5555"
)

generator = TicketReceiptGenerator(business_settings_service=mock_settings)

# Test Data
ticket_data = {
    'ticket_number': 'T-2023-001',
    'print_format': 'Thermal 80mm',
    'customer_name': 'John Doe',
    'customer_phone': '555-0199',
    'device': 'iPhone X',
    'issue_type': 'Screen',
    'description': 'Broken Screen',
    'estimated_cost': 100.0,
    'deposit_paid': 20.0
}

# Generate PDF via WeasyPrint
try:
    print("Generating PDF...")
    generator._print_to_pdf(ticket_data, "test_ticket_weasy.pdf")
    print("PDF Generated successfully: test_ticket_weasy.pdf")
except Exception as e:
    print(f"Error generating PDF: {e}")
