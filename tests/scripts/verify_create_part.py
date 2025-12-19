
import sys
import os
from pathlib import Path

# Add src/app to python path
sys.path.append(os.path.abspath("src/app"))

from peewee import SqliteDatabase
from models.part import Part
from models.category import Category
from models.audit_log import AuditLog
from models.user import User
from services.part_service import PartService
from services.audit_service import AuditService
from services.category_service import CategoryService
from repositories.part_repository import PartRepository
from repositories.category_repository import CategoryRepository
from PySide6.QtCore import QObject

# Mock Container
class Container:
    def __init__(self):
        self.part_service = None
        self.category_service = None

def setup_db():
    # Use an in-memory DB for testing
    test_db = SqliteDatabase(':memory:')
    
    # Bind models to test DB
    models = [Part, Category, AuditLog, User]
    test_db.bind(models)
    test_db.connect()
    test_db.create_tables(models)
    return test_db

def test_create_part_logic():
    print("Setting up test database...")
    db = setup_db()
    
    print("Initializing services...")
    audit_service = AuditService()
    
    # Need repositories for services
    # Note: In real app, services instantiate their own repositories usually, 
    # but here we are testing the service logic directly as used by the dialog
    
    part_service = PartService(audit_service)
    category_service = CategoryService(audit_service)
    
    container = Container()
    container.part_service = part_service
    container.category_service = category_service
    
    # Create a category first
    category = category_service.create_category("Test Category")
    
    # Simulate data from PartDialog
    part_data = {
        'name': "New Part from Dialog",
        'brand': "Test Brand",
        'category': "Test Category", # Service handles name lookup or creation? 
                                     # PartService.create_part expects category ID or name?
                                     # Let's check PartService.create_part signature/logic
        'model_compatibility': "Model X",
        'cost': 10.50,
        'stock': 100,
        'min_stock_level': 5,
        'sku': "SKU-123",
        'barcode': "BAR-123"
    }
    
    print("Attempting to create part...")
    try:
        # PartService.create_part usually takes kwargs matching the model or specific args
        # Let's check PartService.create_part implementation in the file view if needed
        # But assuming standard kwargs:
        
        # Wait, PartDialog logic:
        # part = self.container.part_service.create_part(**part_data)
        
        # Does create_part handle 'category' as string name? 
        # If not, PartDialog might be failing there.
        
        part = part_service.create_part(**part_data)
        
        if part:
            print(f"SUCCESS: Part created. ID: {part.id}, Name: {part.name}")
        else:
            print("FAILURE: Part creation returned None")
            
    except Exception as e:
        print(f"FAILURE: Exception during part creation: {e}")
        import traceback
        traceback.print_exc()

    db.close()

if __name__ == "__main__":
    try:
        test_create_part_logic()
        print("\nAll tests completed.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
