
import time
import statistics
from models.ticket import Ticket
from models.device import Device
from models.customer import Customer
from models.user import User
from models.technician import Technician
from models.branch import Branch
from repositories.ticket_repository import TicketRepository
from config.database import initialize_database, db

def benchmark_tickets(count=500):
    print(f"🚀 Benchmarking Ticket Loading ({count} tickets)...")
    
    if db.is_closed():
        initialize_database()
        
    repo = TicketRepository()
    
    # 1. Seed Data
    print("Seeding data...")
    with db.atomic():
        # Clean up first to be fair? Na, let's just add to existing or use a fresh test db logic.
        # Ideally using test DB.
        
        branch = Branch.create(name="Bench Branch", address="addr", phone="123")
        tech = Technician.create(first_name="Bench", last_name="Tech", full_name="Bench Tech")
        
        # Create users/customers
        customer = Customer.create(name="Bench Customer", email="bench@test.com")
        device = Device.create(customer=customer, brand="Bench", model="Mk1")
        
        # Batch create tickets
        data_list = []
        ts = int(time.time())
        for i in range(count):
            data_list.append({
                "ticket_number": f"BENCH-{ts}-{i}",
                "device": device,
                "branch": branch,
                "assigned_technician": tech,
                "status": "Open",
                "error_description": "Benchmarking"
            })
            
        # Bulk create is faster for setup
        # But Peewee bulk_create doesn't run save() logic (ticket number check). 
        # We manually generated unique numbers so it's fine.
        Ticket.insert_many(data_list).execute()
        
    print("✅ Seeded.")
    
    # 2. Measure Query Time
    start_time = time.perf_counter()
    
    # Simulate Controller listing
    tickets = repo.list_all(filters={'status': 'Open'})
    
    query_time = (time.perf_counter() - start_time) * 1000
    print(f"⏱️  Query Time: {query_time:.2f} ms")
    
    # 3. Measure Iteration (N+1 simulation)
    # Accessing relationships that might trigger lazy loading
    start_iter = time.perf_counter()
    
    for t in tickets:
         _ = t.device.brand  # Potential N+1
         _ = t.device.customer.name # Potential N+1
         if t.assigned_technician:
             _ = t.assigned_technician.full_name # Potential N+1
             
    iter_time = (time.perf_counter() - start_iter) * 1000
    print(f"⏱️  Iteration Time (N+1 Access): {iter_time:.2f} ms")
    
    # cleanup (on test db ideally)
    # Ticket.delete().where(Ticket.ticket_number.startswith("BENCH-")).execute()
    
if __name__ == "__main__":
    benchmark_tickets()
