"""PurchaseReturnItem Model - Purchase Return Line Items."""

from peewee import AutoField, IntegerField, CharField, TextField, DecimalField, ForeignKeyField
from models.base_model import BaseModel
from models.purchase_return import PurchaseReturn
from models.part import Part


class PurchaseReturnItem(BaseModel):
    """Line items for purchase returns."""
    
    id = AutoField(help_text="Primary key")
    purchase_return = ForeignKeyField(PurchaseReturn, backref='items', on_delete='CASCADE', help_text="Purchase return")
    part = ForeignKeyField(Part, backref='return_items', on_delete='CASCADE', help_text="Part")
    quantity = IntegerField(help_text="Quantity returned")
    unit_cost = DecimalField(max_digits=10, decimal_places=2, help_text="Unit cost")
    total_cost = DecimalField(max_digits=10, decimal_places=2, help_text="Total cost")
    condition = CharField(max_length=20, default='defective', help_text="Item condition")
    notes = TextField(null=True, help_text="Notes")
    
    class Meta:
        table_name = 'purchase_return_items'
    
    def save(self, *args, **kwargs):
        self.total_cost = float(self.quantity) * float(self.unit_cost)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.part.name} x{self.quantity}"
