
import pytest
from models.branch import Branch
from models.user import User
from models.ticket import Ticket
from models.customer import Customer
from models.device import Device
from repositories.ticket_repository import TicketRepository
from services.auth_service import AuthService
from config.database import db

def verify_branch_management():
    print("🚀 Starting Branch Management Verification...")
    
    # 1. Setup Test Data
    print("\n1. Setting up test data...")
    if db.is_closed():
        db.connect()
        
    # Create Branch
    branch_name = "Test Branch Alpha"
    branch = Branch.create(
        name=branch_name,
        address="123 Test St",
        phone="555-0101"
    )
    print(f"✅ Created Branch: {branch.name} (ID: {branch.id})")
    
    # Create User linked to Branch
    username = "branch_manager_test"
    email = "manager@test.com"
    
    # Clean up existing user if any
    existing = User.get_or_none(User.username == username)
    if existing:
        existing.delete_instance()
        
    user = User.create(
        username=username,
        email=email,
        full_name="Branch Manager",
        password_hash="hash",
        branch=branch
    )
    print(f"✅ Created User: {user.username} linked to Branch ID: {user.branch.id}")
    
    # Verify User-Branch Link
    retrieved_user = User.get_by_id(user.id)
    assert retrieved_user.branch.id == branch.id
    print("✅ Verified User-Branch link persistence.")
    
    # 2. Verify Ticket Filtering
    print("\n2. Verifying Ticket Filtering...")
    
    # Create prerequisites
    customer = Customer.create(name="Test Customer", email="cust@test.com")
    device = Device.create(customer=customer, brand="Test", model="Phone")
    
    # Create Ticket for Branch
    ticket = Ticket.create(
        ticket_number="TEST-001",
        device=device,
        branch=branch,
        created_by=user,
        issue="Screen Crack"
    )
    print(f"✅ Created Ticket {ticket.ticket_number} for Branch ID: {branch.id}")
    
    # Create Ticket for NO Branch (Global)
    ticket_global = Ticket.create(
        ticket_number="TEST-002",
        device=device,
        branch=None,
        created_by=user,
        issue="Battery"
    )
    print(f"✅ Created Global Ticket {ticket_global.ticket_number}")
    
    repo = TicketRepository()
    
    # Test Filter: Specific Branch
    branch_tickets = repo.list_all(filters={'branch_id': branch.id})
    assert len(branch_tickets) == 1
    assert branch_tickets[0].id == ticket.id
    print(f"✅ Filtered by Branch ID {branch.id}: Found {len(branch_tickets)} ticket(s) (Correct).")
    
    # Test Filter: Other Branch (should be empty)
    other_branch_tickets = repo.list_all(filters={'branch_id': 99999})
    assert len(other_branch_tickets) == 0
    print(f"✅ Filtered by Non-existent Branch: Found {len(other_branch_tickets)} ticket(s) (Correct).")
    
    # Test Filter: None (All tickets? Or just global? list_all implementation logic)
    # The implementation was:
    # if 'branch_id' in filters and filters['branch_id']:
    #    query = query.where(Ticket.branch == filters['branch_id'])
    # So if branch_id is NOT in filters, it returns ALL.
    
    all_tickets = repo.list_all(filters={})
    # We might have other tickets in DB, so just check if our created ones are there
    ids = [t.id for t in all_tickets]
    assert ticket.id in ids
    assert ticket_global.id in ids
    print(f"✅ No Filter: Found both tickets (Correct).")

    # 3. Cleanup
    print("\n3. Cleaning up...")
    ticket.delete_instance()
    ticket_global.delete_instance()
    device.delete_instance()
    customer.delete_instance()
    user.delete_instance()
    branch.delete_instance()
    print("✅ Cleanup complete.")
    
    print("\n✨ Branch Management Verification PASSED!")

if __name__ == "__main__":
    verify_branch_management()
