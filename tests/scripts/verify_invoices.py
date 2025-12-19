import sys
import os

# Add src to path
sys.path.append(os.path.abspath('src/app'))

try:
    from core.dependency_container import DependencyContainer
    
    print("Initializing DependencyContainer...")
    container = DependencyContainer()
    
    print("Getting invoice_service...")
    invoice_service = container.invoice_service
    
    print("Listing invoices...")
    invoices = invoice_service.list_invoices()
    print(f"Found {len(invoices)} invoices.")
    
    for invoice in invoices:
        print(f"Checking invoice {invoice.invoice_number}...")
        
        # Check relationships
        if invoice.purchase_order:
            print(f"  - PO: {invoice.purchase_order.po_number}")
            if invoice.purchase_order.supplier:
                print(f"  - Supplier: {invoice.purchase_order.supplier.name} (ID: {invoice.purchase_order.supplier.id})")
            else:
                print("  - Supplier: None")
        else:
            print("  - PO: None")
            
        # Check status
        print(f"  - Status: {invoice.status}")
        print(f"  - Outstanding: {invoice.outstanding_amount}")

    print("VERIFICATION COMPLETE")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
