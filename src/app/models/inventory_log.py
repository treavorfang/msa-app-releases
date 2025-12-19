"""InventoryLog Model - Stock Movement Tracking."""

from datetime import datetime
from peewee import AutoField, IntegerField, CharField, TextField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.part import Part
from models.user import User


class InventoryLog(BaseModel):
    """Log of inventory stock movements."""
    
    id = AutoField(help_text="Primary key")
    part = ForeignKeyField(Part, backref='inventory_logs', on_delete='CASCADE', help_text="Part")
    action_type = CharField(choices=['in', 'out', 'adjust'], max_length=10, help_text="Action type")
    quantity = IntegerField(help_text="Quantity changed")
    reference_id = IntegerField(null=True, help_text="Reference ID")
    reference_type = CharField(max_length=50, null=True, help_text="Reference type")
    notes = TextField(null=True, help_text="Notes")
    logged_at = DateTimeField(default=datetime.now, help_text="Log timestamp")
    logged_by = ForeignKeyField(User, backref='inventory_logs', on_delete='SET NULL', null=True, help_text="User")
    
    class Meta:
        table_name = 'inventory_logs'
        indexes = ((('part', 'logged_at'), False),)
    
    def __str__(self):
        return f"{self.action_type} {self.quantity} {self.part.name}"