import sys
import os
from datetime import datetime, timedelta

# Add src/app to path
sys.path.append(os.path.join(os.getcwd(), 'src', 'app'))

from database.database import db
from services.ticket_service import TicketService
from repositories.ticket_repository import TicketRepository
from models.invoice import Invoice
from peewee import fn

def debug_revenue():
    print("--- Starting Debug ---")
    
    # Initialize Service
    repo = TicketRepository()
    service = TicketService(repo, None) # We typically inject event_bus as 2nd arg
    
    # 1. Check Invoice Count
    count = Invoice.select().count()
    print(f"Total Invoices in DB: {count}")
    
    if count == 0:
        print("No invoices found! Create one first.")
        return

    # 2. Get Date Range (Last 30 Days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    print(f"Querying Range: {start_date} to {end_date}")
    
    # 3. Test get_dashboard_stats_range (Total Revenue Card logic)
    stats = repo.get_dashboard_stats_range(start_date, end_date)
    print(f"Dashboard Stats Revenue: {stats.get('revenue')}")
    
    # 4. Test get_revenue_trend (Chart logic)
    trend = repo.get_revenue_trend(start_date, end_date)
    print(f"Revenue Trend Result (First 5): {trend[:5]}")
    
    # 5. Check Raw SQL Output for trend
    print("--- Raw SQL Check ---")
    query = (Invoice
        .select(
            fn.DATE(Invoice.created_at).alias('date'),
            fn.SUM(Invoice.total).alias('revenue')
        )
        .group_by(fn.DATE(Invoice.created_at))
    )
    for row in query:
        print(f"Date: {row.date}, Revenue: {row.revenue}")

if __name__ == "__main__":
    debug_revenue()
