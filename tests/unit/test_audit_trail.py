
import pytest
from datetime import datetime, timedelta
from models.audit_log import AuditLog
from models.user import User
from config.database import db
from services.audit_service import AuditService

@pytest.fixture
def clean_audit_db():
    if db.is_closed():
        db.connect()
    with db.atomic() as txn:
        yield
        txn.rollback()

def test_log_creation_and_retrieval(clean_audit_db):
    print("🚀 Starting Audit Log Verification...")
    
    # 1. Setup
    service = AuditService()
    user = User.create(username="auditor", email="audit@test.com", full_name="Auditor", password_hash="hash")
    
    # 2. Key Actions to Verify
    
    # Action A: User Login
    log1 = service.log_action(
        user=user,
        action="login_success",
        table_name="users",
        ip_address="192.168.1.1"
    )
    assert log1.id is not None
    print(f"✅ Logged 'login_success' (ID: {log1.id})")
    
    # Action B: Create Record (with JSON data)
    new_data = {"id": 100, "name": "Test Item", "price": 50.0}
    log2 = service.log_action(
        user=user,
        action="item_create",
        table_name="items",
        new_data=new_data
    )
    assert log2.new_data['name'] == "Test Item"
    print(f"✅ Logged 'item_create' with JSON data (ID: {log2.id})")
    
    # Action C: Update Record (Old + New data)
    old_data = {"id": 100, "name": "Test Item", "price": 50.0}
    updated_data = {"id": 100, "name": "Test Item Updated", "price": 55.0}
    log3 = service.log_action(
        user=user,
        action="item_update",
        table_name="items",
        old_data=old_data,
        new_data=updated_data
    )
    assert log3.old_data['price'] == 50.0
    assert log3.new_data['price'] == 55.0
    print(f"✅ Logged 'item_update' diff (ID: {log3.id})")
    
    # 3. Verify Filters
    
    # Filter by user
    user_logs = service.get_logs_for_user(user.id)
    assert len(user_logs) >= 3
    print(f"✅ Filter by User: Found {len(user_logs)} logs.")
    
    # Filter by table
    item_logs = service.get_logs_for_table("items")
    # Should find create and update
    assert len(item_logs) >= 2
    print(f"✅ Filter by Table 'items': Found {len(item_logs)} logs.")
    
    # Recent logs
    recent = service.get_recent_logs(days=1)
    assert len(recent) >= 3
    print(f"✅ Recent logs found.")

if __name__ == "__main__":
    test_log_creation_and_retrieval(None) # Manual run helper
