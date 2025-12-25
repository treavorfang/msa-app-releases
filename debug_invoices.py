import sys
import os
import asyncio
from peewee import prefetch

sys.path.append(os.path.join(os.getcwd(), "src", "app"))
print(f"Path: {sys.path}")

# Import models
from models.invoice import Invoice
from models.payment import Payment
from models.device import Device
from models.customer import Customer
from config.database import db

def test_list_invoices():
    print("Testing list_invoices logic...")
    try:
        query = Invoice.select().order_by(Invoice.created_at.desc())
        
        # Simulate limit/offset
        invoices = query.limit(20).offset(0)
        
        # Test Prefetch
        print("Executing prefetch...")
        invoices_with_payments = prefetch(invoices, Payment)
        
        results = []
        for inv in invoices_with_payments:
            print(f"Processing Invoice {inv.id}")
            # Calculate Paid Amount
            paid_amount = sum(float(p.amount) for p in inv.payments)
            print(f"  Paid: {paid_amount}")
            
            total = float(inv.total)
            balance = max(0.0, total - paid_amount)
            
            customer_name = "Walk-in"
            if inv.device:
                print(f"  Device: {inv.device.id}")
                if inv.device.customer:
                    customer_name = inv.device.customer.name
                    print(f"  Customer: {customer_name}")
            
            results.append({
                "id": inv.id,
                "paid": paid_amount
            })
            
        print(f"Success! Processed {len(results)} invoices.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    db.init("database/msa_dev.db")
    db.connect()
    test_list_invoices()
