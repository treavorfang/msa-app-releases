"""TechnicianBonus Model - Technician Bonus Tracking."""

from datetime import datetime
from peewee import AutoField, CharField, TextField, DecimalField, BooleanField, ForeignKeyField, DateField, DateTimeField
from models.base_model import BaseModel
from models.technician import Technician
from models.user import User


class TechnicianBonus(BaseModel):
    """Bonuses awarded to technicians."""
    
    id = AutoField(help_text="Primary key")
    technician = ForeignKeyField(Technician, backref='bonuses', on_delete='CASCADE', help_text="Technician")
    bonus_type = CharField(
        max_length=50,
        choices=[('performance', 'Performance'), ('quality', 'Quality'), ('revenue', 'Revenue'), ('custom', 'Custom')],
        help_text="Bonus type"
    )
    amount = DecimalField(max_digits=10, decimal_places=2, help_text="Bonus amount")
    reason = TextField(null=True, help_text="Reason for bonus")
    period_start = DateField(null=True, help_text="Period start")
    period_end = DateField(null=True, help_text="Period end")
    awarded_date = DateTimeField(default=datetime.now, help_text="Award date")
    paid = BooleanField(default=False, help_text="Paid status")
    paid_date = DateTimeField(null=True, help_text="Payment date")
    notes = TextField(null=True, help_text="Notes")
    created_at = DateTimeField(default=datetime.now, help_text="Creation timestamp")
    created_by = ForeignKeyField(User, backref='bonuses_created', on_delete='SET NULL', null=True, help_text="Creator")
    
    class Meta:
        table_name = 'technician_bonuses'
        indexes = ((('technician', 'awarded_date'), False), (('bonus_type',), False))
    
    def __str__(self):
        return f"{self.technician.full_name} - {self.bonus_type} - {self.amount}"
