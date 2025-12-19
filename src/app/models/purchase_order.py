"""PurchaseOrder Model - Supplier Order Management."""

from datetime import datetime
from peewee import AutoField, CharField, TextField, DecimalField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.supplier import Supplier
from models.branch import Branch
from models.user import User
from config.constants import PurchaseOrderStatus


class PurchaseOrder(BaseModel):
    """Purchase order for ordering parts from suppliers."""
    
    id = AutoField(help_text="Primary key")
    po_number = CharField(max_length=50, unique=True, help_text="PO number")
    supplier = ForeignKeyField(Supplier, backref='purchase_orders', on_delete='SET NULL', null=True, help_text="Supplier")
    status = CharField(
        choices=PurchaseOrderStatus.ALL,
        default=PurchaseOrderStatus.DRAFT,
        max_length=20,
        help_text="Order status"
    )
    order_date = DateTimeField(default=datetime.now, help_text="Order date")
    expected_delivery = DateTimeField(null=True, help_text="Expected delivery date")
    received_date = DateTimeField(null=True, help_text="Actual received date")
    total_amount = DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Total amount")
    notes = TextField(null=True, help_text="Order notes")
    branch = ForeignKeyField(Branch, backref='purchase_orders', on_delete='SET NULL', null=True, help_text="Branch")
    created_by = ForeignKeyField(User, backref='purchase_orders_created', on_delete='SET NULL', null=True, help_text="Creator")
    
    class Meta:
        table_name = 'purchase_orders'
        indexes = ((('po_number',), True),)
    
    @classmethod
    def generate_po_number(cls, branch_id=None):
        """Generate PO number using custom format from BusinessSettings."""
        import re
        from models.business_settings import BusinessSettings
        
        # Get custom format from settings
        settings = BusinessSettings.select().first()
        fmt = settings.po_number_format if settings else "PO-{branch}{date}-{seq}"
        
        today = datetime.now().strftime("%y%m%d")
        if branch_id is None:
            branch_id = 1
        elif hasattr(branch_id, 'id'):
            branch_id = branch_id.id
            
        last_po = cls.select().order_by(cls.po_number.desc()).first()
        sequence = 1
        if last_po:
            match = re.search(r"(\d{4})$", last_po.po_number)
            if match:
                sequence = int(match.group(1)) + 1
                if sequence > 9999:
                    sequence = 1
        
        return fmt.format(
            branch=branch_id,
            date=today,
            seq=f"{sequence:04d}"
        )

    def save(self, *args, **kwargs):
        if not self.po_number:
            self.po_number = self.generate_po_number(self.branch)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.po_number