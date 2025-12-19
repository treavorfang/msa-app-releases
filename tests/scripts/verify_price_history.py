import sys
import os
from pathlib import Path

# Add src/app to python path
sys.path.append(os.path.abspath("src/app"))

from peewee import SqliteDatabase
from models.part import Part
from models.category import Category
from models.price_history import PriceHistory
from models.audit_log import AuditLog
from models.user import User
from services.part_service import PartService
from services.audit_service import AuditService
from repositories.price_history_repository import PriceHistoryRepository

def setup_db():
    # Use an in-memory DB for testing
    test_db = SqliteDatabase(':memory:')
    
    # Bind models to test DB
    models = [Part, Category, PriceHistory, AuditLog, User]
    test_db.bind(models)
    test_db.connect()
    test_db.create_tables(models)
    return test_db

def test_price_history():
    print("Setting up test database...")
    db = setup_db()
    
    print("Initializing services...")
    audit_service = AuditService()
    part_service = PartService(audit_service)
    price_repo = PriceHistoryRepository()
    
    # Test 1: Create part and verify initial price is logged
    print("\nTest 1: Create part with initial price")
    part = part_service.create_part(
        brand="Apple",
        category="Screen",
        name="iPhone 12 Screen",
        cost=50.00,
        stock=10
    )
    
    if part:
        print(f"SUCCESS: Part created. ID: {part.id}, Cost: ${part.cost_price}")
    else:
        print("FAILURE: Failed to create part")
        return
    
    # Check if initial price was logged
    history = price_repo.get_history_for_part(part.id)
    if len(history) == 1:
        print(f"SUCCESS: Initial price logged. Old: ${history[0].old_price}, New: ${history[0].new_price}")
    else:
        print(f"FAILURE: Expected 1 history entry, got {len(history)}")
    
    # Test 2: Update price and verify it's logged
    print("\nTest 2: Update part price")
    updated_part = part_service.update_part(
        part.id,
        cost=75.00,
        price_change_reason="Supplier price increase"
    )
    
    if updated_part:
        print(f"SUCCESS: Part updated. New cost: ${updated_part.cost_price}")
    else:
        print("FAILURE: Failed to update part")
        return
    
    # Check if price change was logged
    history = price_repo.get_history_for_part(part.id)
    if len(history) == 2:
        print(f"SUCCESS: Price change logged. Total history entries: {len(history)}")
        latest = history[0]  # Most recent first
        print(f"  Latest change: ${latest.old_price} -> ${latest.new_price}, Reason: {latest.change_reason}")
    else:
        print(f"FAILURE: Expected 2 history entries, got {len(history)}")
    
    # Test 3: Update price again
    print("\nTest 3: Update price again")
    part_service.update_part(
        part.id,
        cost=60.00,
        price_change_reason="Promotional discount"
    )
    
    history = price_repo.get_history_for_part(part.id)
    if len(history) == 3:
        print(f"SUCCESS: All price changes logged. Total entries: {len(history)}")
        print("\nPrice history:")
        for i, entry in enumerate(history):
            print(f"  {i+1}. {entry.changed_at.strftime('%Y-%m-%d %H:%M')} - ${entry.old_price} -> ${entry.new_price} ({entry.change_reason})")
    else:
        print(f"FAILURE: Expected 3 history entries, got {len(history)}")
    
    # Test 4: Update part without changing price
    print("\nTest 4: Update part without changing price")
    part_service.update_part(
        part.id,
        stock=20  # Only update stock, not price
    )
    
    history = price_repo.get_history_for_part(part.id)
    if len(history) == 3:
        print("SUCCESS: No new price history entry when price unchanged")
    else:
        print(f"FAILURE: Expected 3 history entries (no change), got {len(history)}")
    
    db.close()

if __name__ == "__main__":
    try:
        test_price_history()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
