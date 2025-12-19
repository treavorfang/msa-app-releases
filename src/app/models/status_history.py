"""StatusHistory Model - Ticket Status Change Tracking."""

from datetime import datetime
from peewee import AutoField, CharField, TextField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.ticket import Ticket
from models.user import User


class StatusHistory(BaseModel):
    """Audit log for ticket status changes."""
    
    id = AutoField(help_text="Primary key")
    ticket = ForeignKeyField(Ticket, backref='status_history', on_delete='CASCADE', help_text="Ticket")
    old_status = CharField(max_length=50, help_text="Previous status")
    new_status = CharField(max_length=50, help_text="New status")
    reason = TextField(null=True, help_text="Reason for change")
    changed_by = ForeignKeyField(User, backref='status_history_changes', on_delete='SET NULL', null=True, help_text="User who made change")
    changed_at = DateTimeField(default=datetime.now, help_text="Change timestamp")
    
    class Meta:
        table_name = 'status_history'
    
    def __str__(self):
        return f"{self.old_status} → {self.new_status}"