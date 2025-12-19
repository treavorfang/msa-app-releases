"""BusinessSettings Model - Business Configuration."""

from peewee import CharField, TextField, DecimalField, ForeignKeyField
from models.base_model import BaseModel
from models.user import User


class BusinessSettings(BaseModel):
    """Business settings and configuration."""
    
    business_name = CharField(help_text="Business name")
    business_phone = CharField(max_length=20, null=True, help_text="Business phone")
    address = TextField(null=True, help_text="Business address")
    tax_id = CharField(null=True, help_text="Tax ID")
    logo_url = CharField(null=True, help_text="Logo URL")
    notes = CharField(null=True, help_text="Additional notes")
    default_tax_rate = DecimalField(decimal_places=2, default=0, help_text="Default tax rate %")
    create_by = ForeignKeyField(User, backref="created", null=True, help_text="Creator")
    
    class Meta:
        table_name = 'business_settings'
    
    def __str__(self):
        return self.business_name