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
    
    # Custom Numbering Formats
    ticket_number_format = CharField(default="RPT-{branch}{date}-{seq}", help_text="Ticket number format")
    invoice_number_format = CharField(default="INV-{branch}{date}-{seq}", help_text="Invoice number format")
    po_number_format = CharField(default="PO-{branch}{date}-{seq}", help_text="PO number format")
    
    # Custom Terms and Conditions
    ticket_terms = TextField(null=True, help_text="Ticket terms and conditions")
    invoice_terms = TextField(null=True, help_text="Invoice terms and conditions")
    
    create_by = ForeignKeyField(User, backref="created", null=True, help_text="Creator")
    
    class Meta:
        table_name = 'business_settings'
    
    def __str__(self):
        return self.business_name