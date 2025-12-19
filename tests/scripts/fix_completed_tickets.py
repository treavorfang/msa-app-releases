#!/usr/bin/env python3
"""
Script to fix existing completed tickets that are missing the completed_at timestamp.
This will set completed_at to the current time for all completed tickets where it's NULL.
"""

import sys
import os
from datetime import datetime

# Add the src/app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'app'))

from models.ticket import Ticket
from config.database import db

def fix_completed_tickets():
    """Fix completed tickets that are missing completed_at timestamp"""
    
    # Connect to database
    db.connect(reuse_if_open=True)
    
    try:
        # Find all completed tickets without completed_at
        tickets_to_fix = Ticket.select().where(
            (Ticket.status == 'completed') &
            (Ticket.completed_at.is_null())
        )
        
        count = tickets_to_fix.count()
        
        if count == 0:
            print("✓ No tickets need fixing. All completed tickets have completed_at set.")
            return
        
        print(f"Found {count} completed ticket(s) missing completed_at timestamp.")
        print("Fixing tickets...")
        
        fixed_count = 0
        for ticket in tickets_to_fix:
            # Set completed_at to current time
            # Ideally we'd use updated_at or created_at, but current time is safer
            ticket.completed_at = datetime.now()
            ticket.save()
            fixed_count += 1
            print(f"  ✓ Fixed ticket #{ticket.ticket_number} (ID: {ticket.id})")
        
        print(f"\n✓ Successfully fixed {fixed_count} ticket(s)!")
        print("\nNote: The completed_at timestamp was set to the current time.")
        print("If you need more accurate timestamps, you may want to manually update them.")
        
    except Exception as e:
        print(f"✗ Error fixing tickets: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Fix Completed Tickets Missing Timestamp")
    print("=" * 60)
    print()
    
    fix_completed_tickets()
