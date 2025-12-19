"""InvoiceItem Model - Invoice Line Items."""

from peewee import AutoField, IntegerField, CharField, DecimalField, ForeignKeyField
from models.base_model import BaseModel
from models.invoice import Invoice


class InvoiceItem(BaseModel):
    """Line items for invoices."""
    
    id = AutoField(help_text="Primary key")
    invoice = ForeignKeyField(Invoice, backref='items', on_delete='CASCADE', help_text="Parent invoice")
    item_id = IntegerField(help_text="ID of the item (part or service)")
    item_type = CharField(max_length=50, help_text="Type: 'part' or 'service'")
    quantity = IntegerField(default=1, help_text="Quantity")
    unit_price = DecimalField(max_digits=10, decimal_places=2, help_text="Unit price")
    total = DecimalField(max_digits=10, decimal_places=2, help_text="Line total")
    
    class Meta:
        table_name = 'invoice_items'
        indexes = ((('item_type', 'item_id'), False),)
    
    def __str__(self):
        return f"{self.item_type} x{self.quantity} = {self.total}"