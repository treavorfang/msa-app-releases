"""WorkLog Model - Technician Time Tracking."""

from datetime import datetime
from peewee import AutoField, TextField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.technician import Technician
from models.ticket import Ticket


class WorkLog(BaseModel):
    """Work log for tracking technician time on tickets."""
    
    id = AutoField(help_text="Primary key")
    technician = ForeignKeyField(Technician, backref='work_logs', on_delete='CASCADE', help_text="Technician")
    ticket = ForeignKeyField(Ticket, backref='work_logs', on_delete='CASCADE', help_text="Ticket")
    start_time = DateTimeField(default=datetime.now, help_text="Work start time")
    end_time = DateTimeField(null=True, help_text="Work end time")
    work_performed = TextField(help_text="Description of work performed")
    
    class Meta:
        table_name = 'work_logs'
    
    def __str__(self):
        return f"{self.technician.full_name} - {self.ticket.ticket_number}"