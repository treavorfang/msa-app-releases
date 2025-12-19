"""Payment Model - Payment Transaction Tracking."""

from datetime import datetime
from peewee import AutoField, CharField, TextField, DecimalField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.invoice import Invoice
from models.user import User


class Payment(BaseModel):
    """Payment model for invoice payments."""
    
    id = AutoField(help_text="Primary key")
    invoice = ForeignKeyField(Invoice, backref='payments', on_delete='CASCADE', help_text="Associated invoice")
    amount = DecimalField(max_digits=10, decimal_places=2, help_text="Payment amount")
    payment_method = CharField(max_length=50, help_text="Payment method (cash, card, transfer)")
    transaction_id = CharField(max_length=100, null=True, help_text="Transaction ID")
    notes = TextField(null=True, help_text="Payment notes")
    paid_at = DateTimeField(default=datetime.now, help_text="Payment timestamp")
    received_by = ForeignKeyField(User, backref='payments_received', on_delete='SET NULL', null=True, help_text="User who received payment")
    
    class Meta:
        table_name = 'payments'
    
    def __str__(self):
        return f"Payment {self.amount} for {self.invoice.invoice_number}"