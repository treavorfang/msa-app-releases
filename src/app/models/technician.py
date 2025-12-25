"""Technician Model - Technician Management."""

from datetime import datetime
from peewee import AutoField, CharField, TextField, DecimalField, BooleanField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel


class Technician(BaseModel):
    """Technician model for repair staff management."""
    
    id = AutoField(help_text="Primary key")
    full_name = CharField(max_length=255, help_text="Full name")
    email = CharField(max_length=255, null=True, unique=True, help_text="Email address")
    phone = CharField(max_length=20, null=True, help_text="Phone number")
    address = TextField(null=True, help_text="Address")
    password = CharField(max_length=255, null=True, help_text="Hashed password")
    profile_photo = CharField(max_length=500, null=True, help_text="Profile photo path")
    certification = CharField(max_length=255, null=True, help_text="Certifications")
    specialization = CharField(max_length=255, null=True, help_text="Specializations")
    salary = DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Base salary")
    commission_rate = DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Commission rate %")
    is_active = BooleanField(default=True, help_text="Active status")
    joined_at = DateTimeField(default=datetime.now, help_text="Employment start date")
    left_at = DateTimeField(null=True, help_text="Employment end date")
    created_at = DateTimeField(default=datetime.now, help_text="Creation timestamp")
    updated_at = DateTimeField(default=datetime.now, help_text="Update timestamp")
    deleted_at = DateTimeField(null=True, help_text="Soft delete timestamp")
    created_by = ForeignKeyField('self', null=True, backref='technicians_created', help_text="Creator")
    updated_by = ForeignKeyField('self', null=True, backref='technicians_updated', help_text="Last updater")
    
    # NEW: Link to User System
    from models.user import User
    user = ForeignKeyField(User, backref='technician_profile', null=True, unique=True, help_text="Linked User Account")

    class Meta:
        table_name = 'technicians'
    
    def __str__(self):
        # Fallback to local name if not linked, else use User name
        if self.user:
            return self.user.full_name
        return self.full_name