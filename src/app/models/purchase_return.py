"""PurchaseReturn Model - Supplier Return Management."""

from datetime import datetime
from peewee import AutoField, CharField, TextField, DecimalField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.purchase_order import PurchaseOrder
from models.user import User


class PurchaseReturn(BaseModel):
    """Returns to suppliers."""
    
    id = AutoField(help_text="Primary key")
    return_number = CharField(max_length=50, unique=True, help_text="Return number")
    purchase_order = ForeignKeyField(PurchaseOrder, backref='returns', on_delete='CASCADE', help_text="Purchase order")
    return_date = DateTimeField(default=datetime.now, help_text="Return date")
    reason = TextField(help_text="Return reason")
    status = CharField(max_length=20, default='draft', help_text="Status")
    total_amount = DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Total amount")
    notes = TextField(null=True, help_text="Notes")
    created_by = ForeignKeyField(User, backref='purchase_returns_created', on_delete='SET NULL', null=True, help_text="Creator")
    created_at = DateTimeField(default=datetime.now, help_text="Creation timestamp")
    approved_by = ForeignKeyField(User, backref='purchase_returns_approved', on_delete='SET NULL', null=True, help_text="Approver")
    approved_at = DateTimeField(null=True, help_text="Approval timestamp")
    
    class Meta:
        table_name = 'purchase_returns'
        indexes = ((('return_number',), True),)
    
    def save(self, *args, **kwargs):
        if self.status == 'approved' and not self.approved_at:
            self.approved_at = datetime.now()
        super().save(*args, **kwargs)
    
    @property
    def supplier(self):
        return self.purchase_order.supplier if self.purchase_order else None
    
    def __str__(self):
        return self.return_number
