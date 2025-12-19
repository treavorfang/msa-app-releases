"""CreditNote Model - Supplier Credit Management."""

from datetime import datetime
from peewee import AutoField, CharField, TextField, DecimalField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.purchase_return import PurchaseReturn
from models.supplier_invoice import SupplierInvoice


class CreditNote(BaseModel):
    """Credit notes from suppliers."""
    
    id = AutoField(help_text="Primary key")
    credit_note_number = CharField(max_length=50, unique=True, help_text="Credit note number")
    purchase_return = ForeignKeyField(PurchaseReturn, backref='credit_notes', on_delete='CASCADE', help_text="Purchase return")
    supplier_invoice = ForeignKeyField(SupplierInvoice, backref='credit_notes', on_delete='SET NULL', null=True, help_text="Supplier invoice")
    credit_amount = DecimalField(max_digits=10, decimal_places=2, help_text="Credit amount")
    applied_amount = DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Amount used")
    remaining_credit = DecimalField(max_digits=10, decimal_places=2, help_text="Available credit")
    status = CharField(max_length=20, default='pending', help_text="Status")
    issue_date = DateTimeField(default=datetime.now, help_text="Issue date")
    expiry_date = DateTimeField(null=True, help_text="Expiry date")
    notes = TextField(null=True, help_text="Notes")
    
    class Meta:
        table_name = 'credit_notes'
        indexes = ((('credit_note_number',), True),)
    
    def save(self, *args, **kwargs):
        self.remaining_credit = float(self.credit_amount) - float(self.applied_amount)
        if self.remaining_credit <= 0:
            self.status = 'applied'
        elif self.expiry_date and datetime.now() > self.expiry_date:
            self.status = 'expired'
        else:
            self.status = 'pending'
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return self.expiry_date and datetime.now() > self.expiry_date
    
    @property
    def supplier(self):
        return self.purchase_return.supplier if self.purchase_return else None
    
    def __str__(self):
        return self.credit_note_number
