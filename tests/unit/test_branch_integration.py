
import pytest
from models.branch import Branch
from models.user import User
from models.ticket import Ticket
from models.customer import Customer
from models.device import Device
from repositories.ticket_repository import TicketRepository
from config.database import db

@pytest.fixture
def clean_db():
    if db.is_closed():
        db.connect()
    with db.atomic() as txn:
        yield
        txn.rollback()

def test_branch_filtering(clean_db):
    """Test that tickets are correctly filtered by branch"""
    
    # Setup
    branch = Branch.create(name="Test Branch", address="123 Test", phone="555-5555")
    user = User.create(
        username="branch_tester", 
        email="tester@test.com", 
        full_name="Branch Tester",
        password_hash="hash", 
        branch=branch
    )
    customer = Customer.create(name="Test Customer", email="cust@test.com")
    device = Device.create(customer=customer, brand="Test", model="Phone")
    
    # Create Tickets
    t1 = Ticket.create(
        ticket_number="TEST-B1", 
        device=device, 
        branch=branch, 
        created_by=user, 
        issue="Issue 1",
        status="open",
        priority="medium"
    )
    
    t2 = Ticket.create(
        ticket_number="TEST-GL", 
        device=device, 
        branch=None, 
        created_by=user, 
        issue="Issue 2",
        status="open",
        priority="medium"
    )
    
    repo = TicketRepository()
    
    # Assertions
    
    # 1. Filter by Branch ID
    branch_tickets = repo.list_all(filters={'branch_id': branch.id})
    assert len(branch_tickets) == 1
    assert branch_tickets[0].id == t1.id
    
    # 2. Filter by invalid Branch ID
    empty_tickets = repo.list_all(filters={'branch_id': 99999})
    assert len(empty_tickets) == 0
    
    # 3. No Filter (Should return all depending on implementation, usually repo returns all if no filter)
    # Note: repo.list_all() might need explicit handling if we want to default to "Global only" or "All"
    # Currently it returns ALL if filter is missing.
    all_tickets = repo.list_all(filters={})
    ids = [t.id for t in all_tickets]
    assert t1.id in ids
    assert t2.id in ids

def test_user_branch_assignment(clean_db):
    """Test assigning user to a branch"""
    branch = Branch.create(name="User Branch", address="123", phone="555")
    user = User.create(
        username="user_branch_test", 
        email="u@test.com", 
        full_name="User Branch Test",
        password_hash="hash",
        branch=branch
    )
    
    retrieved = User.get_by_id(user.id)
    assert retrieved.branch is not None
    assert retrieved.branch.id == branch.id
