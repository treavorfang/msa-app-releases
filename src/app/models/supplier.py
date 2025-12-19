"""Supplier Model - Supplier Management."""

from datetime import datetime
from peewee import AutoField, CharField, TextField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.branch import Branch
from models.user import User


class Supplier(BaseModel):
    """Supplier model for parts and materials."""
    
    id = AutoField(help_text="Primary key")
    name = CharField(max_length=100, help_text="Supplier name")
    contact_person = CharField(max_length=100, null=True, help_text="Contact person")
    email = CharField(max_length=100, null=True, help_text="Email address")
    phone = CharField(max_length=20, null=True, help_text="Phone number")
    address = CharField(max_length=255, null=True, help_text="Physical address")
    tax_id = CharField(max_length=50, null=True, help_text="Tax ID")
    payment_terms = CharField(max_length=100, null=True, help_text="Payment terms")
    notes = TextField(null=True, help_text="Additional notes")
    branch = ForeignKeyField(Branch, backref='suppliers', on_delete='SET NULL', null=True, help_text="Associated branch")
    created_at = DateTimeField(default=datetime.now, help_text="Creation timestamp")
    created_by = ForeignKeyField(User, backref='suppliers_created', on_delete='SET NULL', null=True, help_text="Creator")
    
    class Meta:
        table_name = 'suppliers'
    
    def __str__(self):
        return self.name