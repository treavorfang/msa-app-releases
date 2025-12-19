
import sys
import os
from pathlib import Path

# Add src/app to python path
sys.path.append(os.path.abspath("src/app"))

from peewee import SqliteDatabase
from models.base_model import BaseModel
from models.supplier import Supplier
from models.audit_log import AuditLog
from models.user import User
from models.branch import Branch
from services.supplier_service import SupplierService
from services.audit_service import AuditService
from controllers.supplier_controller import SupplierController
from PySide6.QtCore import QObject

# Mock Container
class Container:
    def __init__(self):
        self.supplier_service = None
        self.supplier_controller = None

def setup_db():
    # Use an in-memory DB for testing
    test_db = SqliteDatabase(':memory:')
    
    # Bind models to test DB
    models = [Supplier, AuditLog, User, Branch]
    test_db.bind(models)
    test_db.connect()
    test_db.create_tables(models)
    return test_db

def test_create_supplier():
    print("Setting up test database...")
    db = setup_db()
    
    print("Initializing services...")
    audit_service = AuditService()
    supplier_service = SupplierService(audit_service)
    
    container = Container()
    container.supplier_service = supplier_service
    supplier_controller = SupplierController(container)
    container.supplier_controller = supplier_controller
    
    # Test 1: Create via Service (Current UI behavior)
    print("\nTest 1: Create via Service")
    data1 = {
        "name": "Service Supplier",
        "contact_person": "John Doe",
        "email": "john@service.com",
        "phone": "1234567890",
        "address": "123 Service Lane",
        "tax_id": "TAX123",
        "payment_terms": "Net 30",
        "notes": "Created via service"
    }
    
    supplier1 = supplier_service.create_supplier(data1)
    
    if supplier1 and supplier1.id:
        print(f"SUCCESS: Supplier created via service. ID: {supplier1.id}")
    else:
        print("FAILURE: Failed to create supplier via service")
        
    # Verify in DB
    fetched1 = Supplier.get_or_none(Supplier.id == supplier1.id)
    if fetched1 and fetched1.name == "Service Supplier":
        print("VERIFIED: Supplier 1 found in DB with correct name")
    else:
        print("FAILURE: Supplier 1 not found or incorrect data")

    # Test 2: Create via Controller (Proposed UI behavior)
    print("\nTest 2: Create via Controller")
    data2 = {
        "name": "Controller Supplier",
        "contact_person": "Jane Doe",
        "email": "jane@controller.com",
        "phone": "0987654321",
        "address": "456 Controller Blvd",
        "tax_id": "TAX456",
        "payment_terms": "Net 60",
        "notes": "Created via controller"
    }
    
    # Connect signal to verify it emits
    signal_emitted = False
    def on_created(s):
        nonlocal signal_emitted
        signal_emitted = True
        print(f"SIGNAL RECEIVED: Supplier created: {s.name}")
        
    supplier_controller.supplier_created.connect(on_created)
    
    supplier2 = supplier_controller.create_supplier(data2)
    
    if supplier2 and supplier2.id:
        print(f"SUCCESS: Supplier created via controller. ID: {supplier2.id}")
    else:
        print("FAILURE: Failed to create supplier via controller")
        
    if signal_emitted:
        print("SUCCESS: supplier_created signal was emitted")
    else:
        print("FAILURE: supplier_created signal was NOT emitted")

    # Verify in DB
    fetched2 = Supplier.get_or_none(Supplier.id == supplier2.id)
    if fetched2 and fetched2.name == "Controller Supplier":
        print("VERIFIED: Supplier 2 found in DB with correct name")
    else:
        print("FAILURE: Supplier 2 not found or incorrect data")
        
    db.close()

if __name__ == "__main__":
    try:
        test_create_supplier()
        print("\nAll tests completed.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
