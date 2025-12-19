"""PriceHistory Model - Part Price Change Tracking."""

from datetime import datetime
from peewee import AutoField, CharField, DecimalField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.part import Part
from models.user import User


class PriceHistory(BaseModel):
    """Historical price changes for parts."""
    
    id = AutoField(help_text="Primary key")
    part = ForeignKeyField(Part, backref='price_history', on_delete='CASCADE', help_text="Part")
    old_price = DecimalField(max_digits=10, decimal_places=2, help_text="Old price")
    new_price = DecimalField(max_digits=10, decimal_places=2, help_text="New price")
    changed_at = DateTimeField(default=datetime.now, help_text="Change timestamp")
    changed_by = ForeignKeyField(User, backref='price_changes', on_delete='SET NULL', null=True, help_text="User")
    change_reason = CharField(max_length=255, null=True, help_text="Reason for change")
    
    class Meta:
        table_name = 'price_history'
        indexes = ((('part', 'changed_at'), False),)
    
    def __str__(self):
        return f"{self.part.name}: {self.old_price} → {self.new_price}"
