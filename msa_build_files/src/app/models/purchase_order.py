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
    
    def __str__(self):
        return self.po_number