"""SupplierInvoice Model - Supplier Invoice Management."""

from datetime import datetime, timedelta
from peewee import AutoField, CharField, TextField, DecimalField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.purchase_order import PurchaseOrder
from models.user import User
from config.constants import InvoiceStatus, Limits


class SupplierInvoice(BaseModel):
    """Invoices from suppliers."""
    
    id = AutoField(help_text="Primary key")
    purchase_order = ForeignKeyField(PurchaseOrder, backref='invoices', on_delete='CASCADE', help_text="Purchase order")
    invoice_number = CharField(max_length=50, unique=True, help_text="Invoice number")
    invoice_date = DateTimeField(default=datetime.now, help_text="Invoice date")
    due_date = DateTimeField(help_text="Due date")
    subtotal = DecimalField(max_digits=10, decimal_places=2, help_text="Subtotal")
    discount = DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Discount")
    shipping_fee = DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Shipping fee")
    total_amount = DecimalField(max_digits=10, decimal_places=2, help_text="Total amount")
    paid_amount = DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Paid amount")
    status = CharField(choices=InvoiceStatus.ALL, default=InvoiceStatus.PENDING, max_length=20, help_text="Status")
    notes = TextField(null=True, help_text="Notes")
    created_at = DateTimeField(default=datetime.now, help_text="Creation timestamp")
    created_by = ForeignKeyField(User, backref='supplier_invoices_created', on_delete='SET NULL', null=True, help_text="Creator")
    
    class Meta:
        table_name = 'supplier_invoices'
        indexes = ((('invoice_number',), True),)
    
    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = self.invoice_date + timedelta(days=Limits.DEFAULT_INVOICE_DUE_DAYS)
        self.total_amount = float(self.subtotal) + float(self.shipping_fee) - float(self.discount)
        if self.paid_amount >= self.total_amount:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partial'
        elif datetime.now() > self.due_date and self.paid_amount < self.total_amount:
            self.status = 'overdue'
        else:
            self.status = 'pending'
        super().save(*args, **kwargs)
    
    @property
    def outstanding_amount(self):
        return float(self.total_amount) - float(self.paid_amount)
    
    @property
    def is_overdue(self):
        return datetime.now() > self.due_date and self.outstanding_amount > 0
    
    def __str__(self):
        return self.invoice_number
