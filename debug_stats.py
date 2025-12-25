
import os
import sys

# Add src/app to path
sys.path.append(os.path.abspath('src/app'))

from config.database import initialize_database
from models.ticket import Ticket
from models.repair_part import RepairPart
from models.part import Part
from peewee import fn
from datetime import datetime, timedelta

def test_query():
    initialize_database()
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print(f"Testing queries from {start_date} to {end_date}")
    
    try:
        revenue_query = Ticket.select(
            fn.strftime('%Y-%m-%d', Ticket.completed_at).alias('day'),
            fn.SUM(Ticket.actual_cost).alias('total')
        ).where(
            (Ticket.status == 'completed') &
            (Ticket.completed_at >= start_date) &
            (Ticket.is_deleted == False)
        ).group_by(fn.strftime('%Y-%m-%d', Ticket.completed_at))
        
        print("Revenue query created. Fetching...")
        results = list(revenue_query)
        print(f"Revenue results: {len(results)}")
        for item in results:
            print(f"  Day: {item.day}, Total: {item.total}")
            
        # Success if we reach here
        print("Success for Revenue query")
        
    except Exception as e:
        print(f"Revenue query failed: {e}")
        import traceback
        traceback.print_exc()

    try:
        expense_query = RepairPart.select(
            fn.strftime('%Y-%m-%d', RepairPart.installed_at).alias('day'),
            fn.SUM(Part.cost_price * RepairPart.quantity).alias('total')
        ).join(Part).where(
            (RepairPart.installed_at >= start_date)
        ).group_by(fn.strftime('%Y-%m-%d', RepairPart.installed_at))
        
        revenue_data = {datetime.strptime(item.day, '%Y-%m-%d').strftime("%a"): float(item.total or 0.0) for item in revenue_query if item.day}
        expense_data = {datetime.strptime(item.day, '%Y-%m-%d').strftime("%a"): float(item.total or 0.0) for item in expense_query if item.day}
        
        print(f"Processed Revenue Data: {revenue_data}")
        print(f"Processed Expense Data: {expense_data}")
        
        # Success if we reach here
        print("Success for queries and processing")
        
    except Exception as e:
        print(f"Expense query failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_query()
