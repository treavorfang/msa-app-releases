"""RepairPart Model - Parts Used in Repairs."""

from datetime import datetime
from peewee import AutoField, IntegerField, TextField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.ticket import Ticket
from models.part import Part
from models.technician import Technician


class RepairPart(BaseModel):
    """Junction table linking parts to repair tickets."""
    
    id = AutoField(help_text="Primary key")
    ticket = ForeignKeyField(Ticket, backref='repair_parts', on_delete='CASCADE', help_text="Repair ticket")
    part = ForeignKeyField(Part, backref='repair_parts_used', on_delete='SET NULL', null=True, help_text="Part used")
    technician = ForeignKeyField(Technician, backref='parts_installed', on_delete='SET NULL', null=True, help_text="Technician who installed")
    quantity = IntegerField(default=1, help_text="Quantity used")
    installed_at = DateTimeField(default=datetime.now, help_text="Installation timestamp")
    warranty_terms = TextField(null=True, help_text="Warranty terms for this part")
    warranty_ends = DateTimeField(null=True, help_text="Warranty end date")
    
    class Meta:
        table_name = 'repair_parts'
    
    def __str__(self):
        return f"{self.part.name} x{self.quantity} for {self.ticket.ticket_number}"