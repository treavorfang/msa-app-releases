"""PurchaseOrderItem Model - Purchase Order Line Items."""

from peewee import AutoField, IntegerField, DecimalField, ForeignKeyField
from models.base_model import BaseModel
from models.purchase_order import PurchaseOrder
from models.part import Part


class PurchaseOrderItem(BaseModel):
    """Line items for purchase orders."""
    
    id = AutoField(help_text="Primary key")
    purchase_order = ForeignKeyField(PurchaseOrder, backref='items', on_delete='CASCADE', help_text="Purchase order")
    part = ForeignKeyField(Part, backref='purchase_order_items', on_delete='RESTRICT', help_text="Part")
    quantity = IntegerField(default=1, help_text="Quantity ordered")
    unit_cost = DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Unit cost")
    total_cost = DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Total cost")
    received_quantity = IntegerField(default=0, help_text="Quantity received")
    
    class Meta:
        table_name = 'purchase_order_items'
    
    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.part.name} x{self.quantity}"
