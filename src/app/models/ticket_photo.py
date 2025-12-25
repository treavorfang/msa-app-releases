"""TicketPhoto Model - Repair Photo Management."""

from datetime import datetime
from peewee import AutoField, CharField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.ticket import Ticket

class TicketPhoto(BaseModel):
    """Model for storing photos related to repair tickets."""
    
    id = AutoField(help_text="Primary key")
    ticket = ForeignKeyField(Ticket, backref='photos', on_delete='CASCADE', help_text="Associated ticket")
    image_path = CharField(max_length=500, help_text="Path to the photo file")
    photo_type = CharField(max_length=50, default="general", help_text="Type of photo (e.g., before, after, part)")
    description = CharField(max_length=255, null=True, help_text="Optional description")
    created_at = DateTimeField(default=datetime.now, help_text="Creation timestamp")
    
    class Meta:
        table_name = 'ticket_photos'
    
    def __str__(self):
        return f"Photo for {self.ticket.ticket_number} ({self.photo_type})"
