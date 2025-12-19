"""Warranty Model - Warranty Management."""

from peewee import AutoField, IntegerField, CharField, TextField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.supplier import Supplier


class Warranty(BaseModel):
    """Warranty model for devices and parts."""
    
    id = AutoField(help_text="Primary key")
    type = CharField(max_length=50, help_text="Warranty type")
    terms = TextField(null=True, help_text="Warranty terms")
    start_date = DateTimeField(help_text="Start date")
    end_date = DateTimeField(help_text="End date")
    status = CharField(
        choices=['active', 'expired', 'void'],
        default='active',
        max_length=10,
        help_text="Warranty status"
    )
    warrantyable_type = CharField(max_length=50, help_text="Type: 'device' or 'part'")
    warrantyable_id = IntegerField(help_text="ID of device or part")
    supplier = ForeignKeyField(Supplier, backref='warranties', on_delete='SET NULL', null=True, help_text="Supplier")
    
    class Meta:
        table_name = 'warranties'
        indexes = ((('warrantyable_type', 'warrantyable_id'), False),)
    
    def __str__(self):
        return f"{self.type} warranty ({self.status})"