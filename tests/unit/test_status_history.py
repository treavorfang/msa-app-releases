#!/usr/bin/env python3
"""
Test script to verify status history and device status updates
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'app'))

from config.database import db
from models.ticket import Ticket
from models.device import Device
from models.customer import Customer
from models.branch import Branch
from models.user import User
from models.status_history import StatusHistory
from services.ticket_service import TicketService
from services.audit_service import AuditService

def test_status_updates():
    """Test that status changes update device and create history"""
    
    # Initialize services
    audit_service = AuditService()
    ticket_service = TicketService(audit_service=audit_service)
    
    # Get a test ticket (or create one)
    ticket = Ticket.select().first()
    if not ticket:
        print("❌ No tickets found in database. Please create a ticket first.")
        return
    
    print(f"\n📋 Testing with Ticket: {ticket.ticket_number}")
    print(f"   Current Status: {ticket.status}")
    if ticket.device:
        print(f"   Device Status: {ticket.device.status}")
    
    # Get current user
    user = User.select().first()
    
    # Test status change
    print("\n🔄 Changing ticket status to 'in_progress'...")
    updated_ticket = ticket_service.change_ticket_status(
        ticket_id=ticket.id,
        new_status='in_progress',
        reason="Testing status history",
        current_user=user,
        ip_address="127.0.0.1"
    )
    
    if updated_ticket:
        print(f"✅ Ticket status updated to: {updated_ticket.status}")
        
        # Check device status
        ticket_model = Ticket.get_by_id(ticket.id)
        if ticket_model.device:
            device = Device.get_by_id(ticket_model.device.id)
            print(f"✅ Device status updated to: {device.status}")
            if device.status == 'repairing':
                print("   ✓ Device status correctly mapped!")
            else:
                print(f"   ⚠️  Expected 'repairing', got '{device.status}'")
        
        # Check status history
        history = StatusHistory.select().where(
            StatusHistory.ticket == ticket.id
        ).order_by(StatusHistory.changed_at.desc()).first()
        
        if history:
            print(f"✅ Status history created:")
            print(f"   Old Status: {history.old_status}")
            print(f"   New Status: {history.new_status}")
            print(f"   Reason: {history.reason}")
            print(f"   Changed By: {history.changed_by.username if history.changed_by else 'N/A'}")
            print(f"   Changed At: {history.changed_at}")
        else:
            print("❌ No status history found!")
    else:
        print("❌ Failed to update ticket status")
    
    # Test another status change
    print("\n🔄 Changing ticket status to 'completed'...")
    updated_ticket = ticket_service.change_ticket_status(
        ticket_id=ticket.id,
        new_status='completed',
        reason="Testing completion",
        current_user=user,
        ip_address="127.0.0.1"
    )
    
    if updated_ticket:
        print(f"✅ Ticket status updated to: {updated_ticket.status}")
        
        # Check device status
        ticket_model = Ticket.get_by_id(ticket.id)
        if ticket_model.device:
            device = Device.get_by_id(ticket_model.device.id)
            print(f"✅ Device status updated to: {device.status}")
            if device.status == 'repaired':
                print("   ✓ Device status correctly mapped!")
            else:
                print(f"   ⚠️  Expected 'repaired', got '{device.status}'")
        
        # Check all status history for this ticket
        all_history = StatusHistory.select().where(
            StatusHistory.ticket == ticket.id
        ).order_by(StatusHistory.changed_at.desc())
        
        print(f"\n📜 All Status History ({all_history.count()} entries):")
        for h in all_history:
            print(f"   {h.old_status} → {h.new_status} | {h.changed_at} | {h.reason or 'No reason'}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_status_updates()
