import requests
import json
import sys
import os
from datetime import datetime

# Add src/app to path
sys.path.append(os.path.join(os.getcwd(), 'src', 'app'))

from services.part_service import PartService
from services.repair_part_service import RepairPartService
from services.audit_service import AuditService
from models.ticket import Ticket
from models.part import Part
from models.device import Device
from models.customer import Customer
from config.database import initialize_database

BASE_URL = "http://localhost:8000/api"

def setup_data():
    initialize_database()
    
    audit_service = AuditService()
    part_service = PartService(audit_service)
    repair_part_service = RepairPartService(audit_service) # init with dependency if needed? check sig
    
    # Check RepairPartService init
    # It takes (audit_service), or (audit_service, part_service)?
    # In api.routes.tickets: repair_part_service = RepairPartService(audit_service, part_service)
    # Let's check signature to be safe, or just assume standard
    
    print("🛠 Setting up test data via Models/Services...")
    
    # 1. Ensure Dummy Customer/Device
    customer = Customer.get_or_none(Customer.id == 1)
    if not customer:
        customer = Customer.create(name="Test User", phone="123", email="test@test.com")
        
    device = Device.get_or_none(Device.id == 1)
    if not device:
        device = Device.create(customer=customer, brand="Test", model="Phone", status="received")
        
    unique_suffix = datetime.now().strftime('%M%S')
    ticket = Ticket.create(
        ticket_number=f"TEST-{unique_suffix}",
        device=device,
        customer=device.customer,
        status="completed", # Invoice allowed
        priority="medium",
        estimated_cost=200.0,
        actual_cost=200.0, # Ticket total including everything
        deposit_paid=50.0,
        error="Test Issue"
    )
    print(f"✅ Created Ticket {ticket.id} (Est 200, Dep 50)")
    
    # 3. Create Part directly
    # Check if part exists
    part = Part.get_or_none(Part.sku == "TEST-PART-001")
    if not part:
        part = Part.create(
            name="Test Part",
            sku="TEST-PART-001",
            cost_price=100.0,
            sell_price=100.0, # Irrelevant for invoice logic which uses cost * 1.5
            stock_quantity=10,
            category_id=1,
            supplier_id=1
        )
    print(f"✅ Created/Found Part {part.id} (Cost 100)")
    
    # 4. Add Part to Ticket (via RepairPart model directly to avoid service complexity)
    from models.repair_part import RepairPart
    rp = RepairPart.create(
        ticket=ticket,
        part=part,
        quantity=1,
        part_cost=100.0, # Snapshotted cost
        part_price=100.0 # Snapshotted price (base for markup?) No, logic uses part.cost_price from DTO/Model
                         # Wait, logic: parts = part_service.get_parts_used...
                         # In invoices.py: cost = p.part_price or 0. 
                         # repair_part_dto.part_price maps to part.cost_price.
                         # So we ensure part.cost_price is set, and RepairPart links to it.
    )
    print("✅ Part added to ticket")
    
    return ticket.id

def verify():
    # Setup Data
    try:
        ticket_id = setup_data()
    except Exception as e:
        print(f"❌ Setup Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    print(f" Creating Invoice via API for Ticket {ticket_id}...")
    
    # Create Invoice
    try:
        resp = requests.post(f"{BASE_URL}/invoices/from-ticket/{ticket_id}")
        if resp.status_code != 200:
            print(f"❌ API Failed: {resp.text}")
            # Identify if already exists
            if "already exists" in resp.text:
                # Need to find the invoice ID to verify
                print("⚠️ Invoice exists, verifying existing...")
                # How to find? GET /invoices/ and search?
                # Simplify: just fail or assume last invoice
                # But creating a fresh ticket guarantees new invoice usually.
                sys.exit(1)
            sys.exit(1)
            
        data = resp.json()
        invoice_id = data['id']
        print(f"✅ Invoice {invoice_id} Created")
        
        # Verify
        resp = requests.get(f"{BASE_URL}/invoices/{invoice_id}")
        inv = resp.json()
        
        print("🔍 Verifying Invoice Details...")
        
        # 1. Markup Check
        # Part Cost 100 -> Unit Price 150
        part_item = next((i for i in inv['items'] if i['description'] == "Test Part"), None)
        if not part_item:
             print("❌ Part item missing")
        elif part_item['unit_price'] == 150.0:
             print("✅ Markup Verified: 150.0")
        else:
             print(f"❌ Markup Failed: Got {part_item['unit_price']}")
             
        # 2. Labor Check
        # Ticket Total 200. Parts 150 (markup). Labor should be 200 - 150 = 50.
        svc_item = next((i for i in inv['items'] if "Service for Ticket" in i.get('description', '')), None)
        if not svc_item:
             print("❌ Service item missing")
        elif svc_item['unit_price'] == 50.0:
             print("✅ Labor Verified: 50.0")
        else:
             print(f"❌ Labor Failed: Got {svc_item['unit_price']}")
             
        # 3. Deposit Check
        # Ticket Deposit 50.
        dep = next((p for p in inv['payments'] if p['method'] == 'deposit'), None)
        if dep and dep['amount'] == 50.0:
             print("✅ Deposit Verified: 50.0")
        else:
             print(f"❌ Deposit Failed: {dep}")
             
        # 4. Status
        # Total 150+50 = 200. Paid 50. Expect partial.
        if inv['status'] == 'partially_paid':
            print("✅ Status Verified: partially_paid")
        else:
            print(f"❌ Status: {inv['status']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify()
