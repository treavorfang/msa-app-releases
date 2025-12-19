"""Branch Model - Multi-Location Support."""

from peewee import AutoField, CharField
from models.base_model import BaseModel


class Branch(BaseModel):
    """Branch/location model for multi-location support."""
    
    id = AutoField(help_text="Primary key")
    name = CharField(max_length=100, help_text="Branch name")
    address = CharField(max_length=255, null=True, help_text="Branch address")
    phone = CharField(max_length=20, null=True, help_text="Branch phone")
    
    class Meta:
        table_name = 'branches'
    
    def __str__(self):
        return self.name