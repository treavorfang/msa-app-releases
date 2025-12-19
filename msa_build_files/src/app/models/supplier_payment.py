"""SupplierPayment Model - Supplier Payment Tracking."""

from datetime import datetime
from peewee import AutoField, CharField, TextField, DecimalField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.supplier_invoice import SupplierInvoice
from models.user import User


class SupplierPayment(BaseModel):
    """Payments made to suppliers."""
    
    id = AutoField(help_text="Primary key")
    invoice = ForeignKeyField(SupplierInvoice, backref='payments', on_delete='CASCADE', help_text="Supplier invoice")
    payment_date = DateTimeField(default=datetime.now, help_text="Payment date")
    amount = DecimalField(max_digits=10, decimal_places=2, help_text="Payment amount")
    payment_method = CharField(
        choices=[('cash', 'Cash'), ('check', 'Check'), ('bank_transfer', 'Bank Transfer'), ('credit_card', 'Credit Card'), ('other', 'Other')],
        default='bank_transfer',
        max_length=20,
        help_text="Payment method"
    )
    reference_number = CharField(max_length=100, null=True, help_text="Reference number")
    notes = TextField(null=True, help_text="Notes")
    created_at = DateTimeField(default=datetime.now, help_text="Creation timestamp")
    created_by = ForeignKeyField(User, backref='supplier_payments_created', on_delete='SET NULL', null=True, help_text="Creator")
    
    class Meta:
        table_name = 'supplier_payments'
    
    def __str__(self):
        return f"Payment {self.amount} for {self.invoice.invoice_number}"
