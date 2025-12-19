import sys
import os
from pathlib import Path

# Add src/app to python path
sys.path.append(os.path.abspath("src/app"))

from peewee import SqliteDatabase
from models.part import Part
from models.category import Category
from models.price_history import PriceHistory
from models.purchase_order import PurchaseOrder
from models.purchase_order_item import PurchaseOrderItem
from models.supplier import Supplier
from models.audit_log import AuditLog
from models.user import User
from services.part_service import PartService
from services.purchase_order_service import PurchaseOrderService
from services.audit_service import AuditService
from repositories.price_history_repository import PriceHistoryRepository

def setup_db():
    # Use an in-memory DB for testing
    test_db = SqliteDatabase(':memory:')
    
    # Bind models to test DB
    models = [Part, Category, PriceHistory, PurchaseOrder, PurchaseOrderItem, 
              Supplier, AuditLog, User]
    test_db.bind(models)
    test_db.connect()
    test_db.create_tables(models)
    return test_db

def test_po_price_update():
    print("Setting up test database...")
    db = setup_db()
    
    print("Initializing services...")
    audit_service = AuditService()
    part_service = PartService(audit_service)
    po_service = PurchaseOrderService(audit_service, part_service)
    price_repo = PriceHistoryRepository()
    
    # Create a supplier
    supplier = Supplier.create(name="Test Supplier")
    
    # Test 1: Create part with initial price
    print("\nTest 1: Create part with initial price $50")
    part = part_service.create_part(
        brand="Apple",
        category="Screen",
        name="iPhone 12 Screen",
        cost=50.00,
        stock=5
    )
    
    print(f"✓ Part created: {part.name}, Price: ${part.cost_price}, Stock: {part.current_stock}")
    
    # Test 2: Create PO with different unit cost
    print("\nTest 2: Create PO with unit cost $75 (different from part price)")
    po = po_service.create_purchase_order({
        'po_number': 'PO-TEST-001',
        'supplier': supplier.id,
        'status': 'draft'
    })
    
    # Add item to PO
    po_service.add_item(po.id, {
        'part': part.id,
        'quantity': 10,
        'unit_cost': 75.00  # Different from part's current price
    })
    
    print(f"✓ PO created with item: Qty=10, Unit Cost=$75")
    
    # Test 3: Mark PO as sent, then received
    print("\nTest 3: Mark PO as 'sent' then 'received'")
    po_service.update_status(po.id, 'sent')
    print("✓ PO marked as 'sent'")
    
    po_service.update_status(po.id, 'received')
    print("✓ PO marked as 'received'")
    
    # Test 4: Verify part price was updated
    print("\nTest 4: Verify part price was updated")
    updated_part = part_service.get_part_by_id(part.id)
    
    if float(updated_part.cost_price) == 75.00:
        print(f"✅ SUCCESS: Part price updated to ${updated_part.cost_price}")
    else:
        print(f"❌ FAILURE: Part price is ${updated_part.cost_price}, expected $75.00")
        return False
    
    # Test 5: Verify stock was updated
    print("\nTest 5: Verify stock was updated")
    if updated_part.current_stock == 15:  # 5 initial + 10 from PO
        print(f"✅ SUCCESS: Stock updated to {updated_part.current_stock}")
    else:
        print(f"❌ FAILURE: Stock is {updated_part.current_stock}, expected 15")
        return False
    
    # Test 6: Verify price history was created
    print("\nTest 6: Verify price history was created")
    history = price_repo.get_history_for_part(part.id)
    
    if len(history) == 2:  # Initial price + PO receipt update
        print(f"✅ SUCCESS: Price history has {len(history)} entries")
        print("\nPrice history:")
        for i, entry in enumerate(history):
            print(f"  {i+1}. ${entry.old_price} -> ${entry.new_price} - {entry.change_reason}")
    else:
        print(f"❌ FAILURE: Expected 2 history entries, got {len(history)}")
        return False
    
    # Test 7: Verify the latest price change has correct reason
    latest_change = history[0]
    if "PO receipt" in latest_change.change_reason:
        print(f"✅ SUCCESS: Price change reason mentions PO receipt")
    else:
        print(f"❌ FAILURE: Price change reason doesn't mention PO receipt: {latest_change.change_reason}")
        return False
    
    db.close()
    return True

if __name__ == "__main__":
    try:
        success = test_po_price_update()
        if success:
            print("\n" + "="*50)
            print("✅ ALL TESTS PASSED!")
            print("="*50)
        else:
            print("\n" + "="*50)
            print("❌ SOME TESTS FAILED")
            print("="*50)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
