"""
Invoice Model - Customer Billing System.

Manages customer invoices for repair services and parts, including payment tracking,
tax calculations, and financial reporting.

Features:
    - Automatic invoice number generation (INV-YYMMDD-XXXX)
    - Financial calculations (subtotal, tax, discount, total)
    - Payment status tracking
    - Due date management
    - Device and ticket association
    - Branch tracking for multi-location support

Example:
    >>> invoice = Invoice.create(
    ...     subtotal=1000.00,
    ...     tax=100.00,
    ...     discount=50.00,
    ...     total=1050.00,
    ...     device=device,
    ...     branch=branch,
    ...     created_by=user
    ... )
    >>> print(invoice.invoice_number)  # INV-1241207-0001

Database Schema:
    Table: invoices
    Columns: id, invoice_number, subtotal, tax, discount, total,
             payment_status, due_date, paid_date, device_id, branch_id,
             created_by_id, error_description, created_at

Relationships:
    - device: Many-to-One (Invoice -> Device)
    - branch: Many-to-One (Invoice -> Branch)
    - created_by: Many-to-One (Invoice -> User)
    - invoice_items: One-to-Many (Invoice -> InvoiceItem)
    - payments: One-to-Many (Invoice -> Payment)
"""

import re
from datetime import datetime
from peewee import AutoField, CharField, TextField, DecimalField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.user import User
from models.branch import Branch
from models.device import Device


class Invoice(BaseModel):
    """Invoice model for customer billing."""
    
    id = AutoField(help_text="Primary key")
    invoice_number = CharField(max_length=50, unique=True, help_text="Unique invoice number")
    subtotal = DecimalField(max_digits=10, decimal_places=2, help_text="Subtotal before tax and discount")
    tax = DecimalField(max_digits=10, decimal_places=2, help_text="Tax amount")
    discount = DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Discount amount")
    total = DecimalField(max_digits=10, decimal_places=2, help_text="Total amount")
    payment_status = CharField(
        choices=['unpaid', 'partially_paid', 'paid', 'refunded'],
        default='unpaid',
        max_length=20,
        help_text="Payment status"
    )
    due_date = DateTimeField(null=True, help_text="Payment due date")
    paid_date = DateTimeField(null=True, help_text="Date fully paid")
    device = ForeignKeyField(Device, backref='invoices', on_delete='SET NULL', null=True, help_text="Associated device")
    branch = ForeignKeyField(Branch, backref='invoices', on_delete='SET NULL', null=True, help_text="Branch")
    created_by = ForeignKeyField(User, backref='invoices_created', on_delete='SET NULL', null=True, help_text="Creator")
    error_description = TextField(null=True, help_text="Error/issue description")
    created_at = DateTimeField(default=datetime.now, help_text="Creation timestamp")
    
    class Meta:
        table_name = 'invoices'
        indexes = ((('invoice_number',), True),)
    
    @classmethod
    def generate_invoice_number(cls, branch_id=None):
        """Generate invoice number using custom format from BusinessSettings."""
        from models.business_settings import BusinessSettings
        
        # Get custom format from settings
        settings = BusinessSettings.select().first()
        fmt = settings.invoice_number_format if settings else "INV-{branch}{date}-{seq}"
        
        today = datetime.now().strftime("%y%m%d")
        if branch_id is None:
            branch_id = 1
        elif hasattr(branch_id, 'id'):
            branch_id = branch_id.id
            
        last_invoice = cls.select().order_by(cls.invoice_number.desc()).first()
        sequence = 1
        if last_invoice:
            # We try to extract the last sequence if it matches the general pattern
            # Note: This is trickier with dynamic formats. 
            # For now, we assume {seq} is at the end or we match 4 digits.
            match = re.search(r"(\d{4})$", last_invoice.invoice_number)
            if match:
                sequence = int(match.group(1)) + 1
                if sequence > 9999:
                    sequence = 1
        
        # Replace placeholders
        return fmt.format(
            branch=branch_id,
            date=today,
            seq=f"{sequence:04d}"
        )
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number(self.branch)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.invoice_number
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number} total={self.total}>'
    

    def get_balance_due(self):
        """Calculate remaining balance."""
        from models.payment import Payment
        from peewee import fn
        paid = Payment.select(fn.Sum(Payment.amount)).where(Payment.invoice == self).scalar() or 0
        return float(self.total) - float(paid)
    
    def is_fully_paid(self):
        """Check if invoice is fully paid."""
        return self.payment_status == 'paid'