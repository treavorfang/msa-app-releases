"""TechnicianPerformance Model - Monthly Performance Tracking."""

from datetime import datetime
from peewee import AutoField, IntegerField, DecimalField, ForeignKeyField, DateField, DateTimeField
from models.base_model import BaseModel
from models.technician import Technician


class TechnicianPerformance(BaseModel):
    """Monthly performance metrics for technicians."""
    
    id = AutoField(help_text="Primary key")
    technician = ForeignKeyField(Technician, backref='performance_records', on_delete='CASCADE', help_text="Technician")
    month = DateField(help_text="Performance month")
    tickets_completed = IntegerField(default=0, help_text="Tickets completed")
    tickets_pending = IntegerField(default=0, help_text="Tickets pending")
    avg_completion_days = DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Avg completion days")
    avg_customer_rating = DecimalField(max_digits=3, decimal_places=2, default=0.00, help_text="Avg customer rating")
    total_ratings = IntegerField(default=0, help_text="Total ratings")
    revenue_generated = DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Revenue generated")
    commission_earned = DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Commission earned")
    bonuses_earned = DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Bonuses earned")
    efficiency_score = DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Efficiency score")
    created_at = DateTimeField(default=datetime.now, help_text="Creation timestamp")
    updated_at = DateTimeField(default=datetime.now, help_text="Update timestamp")
    
    class Meta:
        table_name = 'technician_performance'
        indexes = ((('technician', 'month'), True),)
    
    def __str__(self):
        return f"{self.technician.full_name} - {self.month}"
