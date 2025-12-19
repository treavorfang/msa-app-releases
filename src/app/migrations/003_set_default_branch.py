# Migration: Set default branch for all records
from config.database import db
from models.branch import Branch
from models.ticket import Ticket
from models.device import Device
from models.invoice import Invoice
from models.supplier import Supplier
from models.purchase_order import PurchaseOrder
from models.user import User

def apply(database):
    """Set all NULL branch_ids to Main Branch (ID=1)"""
    print("Running migration: Set default branch for all records...")
    
    # Ensure Main Branch exists
    main_branch = Branch.select().where(Branch.id == 1).first()
    if not main_branch:
        print("ERROR: Main Branch (ID=1) not found. Please run initial schema migration first.")
        return
    
    # Update all records with NULL branch_id to use Main Branch
    models_to_update = [
        (Ticket, "tickets"),
        (Device, "devices"),
        (Invoice, "invoices"),
        (Supplier, "suppliers"),
        (PurchaseOrder, "purchase_orders"),
        (User, "users")
    ]
    
    for model, name in models_to_update:
        try:
            # Check if the model has a branch field
            if hasattr(model, 'branch'):
                count = model.update(branch=1).where(model.branch.is_null()).execute()
                print(f"  ✓ Updated {count} {name} to Main Branch")
        except Exception as e:
            print(f"  ⚠ Could not update {name}: {e}")
    
    print("Migration completed: All records now assigned to Main Branch")

def revert(database):
    """Revert is not needed for this migration"""
    pass
