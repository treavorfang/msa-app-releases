
import sys
import os
from pathlib import Path

# Add src/app to python path
sys.path.append(os.path.abspath("src/app"))

from peewee import SqliteDatabase
from models.purchase_order import PurchaseOrder
from models.purchase_order_item import PurchaseOrderItem
from models.supplier import Supplier
from models.part import Part
from models.audit_log import AuditLog
from models.user import User
from models.branch import Branch
from services.purchase_order_service import PurchaseOrderService
from services.audit_service import AuditService
from controllers.purchase_order_controller import PurchaseOrderController
from PySide6.QtCore import QObject

# Mock Container
class Container:
    def __init__(self):
        self.purchase_order_service = None
        self.purchase_order_controller = None

def setup_db():
    # Use an in-memory DB for testing
    test_db = SqliteDatabase(':memory:')
    
    # Bind models to test DB
    models = [PurchaseOrder, PurchaseOrderItem, Supplier, Part, AuditLog, User, Branch]
    test_db.bind(models)
    test_db.connect()
    test_db.create_tables(models)
    return test_db

def test_po_workflow():
    print("Setting up test database...")
    db = setup_db()
    
    print("Initializing services...")
    audit_service = AuditService()
    po_service = PurchaseOrderService(audit_service)
    
    container = Container()
    container.purchase_order_service = po_service
    po_controller = PurchaseOrderController(container)
    container.purchase_order_controller = po_controller
    
    # Create dummy supplier
    supplier = Supplier.create(name="Test Supplier")
    
    # Test 1: Create PO (Draft)
    print("\nTest 1: Create PO (Draft)")
    data = {
        "po_number": "PO-TEST-001",
        "supplier": supplier.id,
        "status": "draft"
    }
    
    po = po_controller.create_purchase_order(data)
    
    if po and po.status == 'draft':
        print(f"SUCCESS: PO created in draft status. ID: {po.id}")
    else:
        print("FAILURE: Failed to create PO or incorrect status")
        return

    # Test 2: Transition to Sent
    print("\nTest 2: Transition to Sent")
    
    # Connect signal
    status_signal_received = False
    def on_status_changed(po_id, new_status):
        nonlocal status_signal_received
        status_signal_received = True
        print(f"SIGNAL RECEIVED: Status changed to {new_status}")
        
    po_controller.status_changed.connect(on_status_changed)
    
    updated_po = po_controller.update_status(po.id, 'sent')
    
    if updated_po and updated_po.status == 'sent':
        print("SUCCESS: PO status updated to 'sent'")
    else:
        print("FAILURE: Failed to update status to 'sent'")
        
    if status_signal_received:
        print("SUCCESS: status_changed signal was emitted")
    else:
        print("FAILURE: status_changed signal was NOT emitted")

    # Test 3: Transition to Received
    print("\nTest 3: Transition to Received")
    
    # Reset signal flag
    status_signal_received = False
    
    updated_po_2 = po_controller.update_status(po.id, 'received')
    
    if updated_po_2 and updated_po_2.status == 'received':
        print("SUCCESS: PO status updated to 'received'")
    else:
        print("FAILURE: Failed to update status to 'received'")
        
    if updated_po_2.received_date:
        print(f"SUCCESS: Received date set to {updated_po_2.received_date}")
    else:
        print("FAILURE: Received date NOT set")

    db.close()

if __name__ == "__main__":
    try:
        test_po_workflow()
        print("\nAll tests completed.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
