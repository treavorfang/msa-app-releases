import sys
import os
from datetime import datetime

# Add src and src/app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/app')))

from app.core.dependency_container import DependencyContainer
from app.utils.print.invoice_generator import InvoiceGenerator
from app.utils.print.ticket_generator import TicketReceiptGenerator
from app.utils.language_manager import LanguageManager

def verify_localization():
    container = DependencyContainer()
    # container.initialize()
    
    # Initialize real language manager
    lang_manager = LanguageManager()
    
    languages = ['en', 'my', 'ja', 'ko', 'hi', 'th', 'vi', 'zh']
    
    output_dir = "verification_outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Generating localized previews in {output_dir}...")
    
    for lang_code in languages:
        print(f"Testing Language: {lang_code}")
        lang_manager.load_language(lang_code)
        
        # Test getting a key to ensure language loaded
        test_key = lang_manager.get('ticket_receipt.repair_ticket_caps')
        print(f"  - 'REPAIR TICKET' in {lang_code}: {test_key}")
        
        # Create Dummy Data
        invoice_data = {
            'invoice_number': f'INV-{lang_code.upper()}-001',
            'date': datetime.now(),
            'customer_name': 'Test Customer',
            'customer_phone': '123-456-7890',
            'customer_address': '123 Test St',
            'items': [
                {'description': 'Screen Replacement', 'qty': 1, 'unit_price': 100.0, 'total': 100.0},
                {'description': 'Labor', 'qty': 1, 'unit_price': 50.0, 'total': 50.0}
            ],
            'subtotal': 150.0,
            'tax': 15.0,
            'total': 165.0,
            'status': 'Paid'
        }
        
        ticket_data = {
            'ticket_id': f'TKT-{lang_code.upper()}-001',
            'created_at': datetime.now(),
            'customer': {
                'name': 'Test Customer',
                'phone': '123-456-7890'
            },
            'device': {
                'brand': 'Apple',
                'model': 'iPhone 13',
                'password': '1234(pass)'
            },
            'issue': 'Broken Screen',
            'status': 'In Progress'
        }
        
        # Critical Keys to check
        critical_keys = [
            ('ticketreceipt', 'repair_ticket_caps'),
            ('ticketreceipt', 'customer_details_caps'),
            ('ticketreceipt', 'terms_conditions_caps'),
            ('ticketreceipt', 'thank_you'),
            ('invoices', 'invoice_title_caps'),
            ('invoices', 'total_caps'),
            ('invoices', 'balance_due_caps'),
            ('inventory', 'part_details_title'), # Checked in zh.ini chunk 2
            ('reports', 'reports') # Checked in zh.ini chunk 3
        ]
        
        all_passed = True
        for section, key in critical_keys:
            full_key = f"{section}.{key}"
            value = lang_manager.get(full_key)
            if value == full_key or not value:
                print(f"  [FAIL] Missing translation for [{section}] {key}")
                all_passed = False
            else:
                 # Optional: Print value to manually verify it looks like the target language
                 pass
        
        if all_passed:
            print(f"  [PASS] Critical keys verified for {lang_code}")

if __name__ == "__main__":
    verify_localization()
