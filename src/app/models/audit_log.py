"""AuditLog Model - System Audit Trail."""

import json
from datetime import datetime
from peewee import AutoField, CharField, TextField, ForeignKeyField, DateTimeField
from models.base_model import BaseModel
from models.user import User


class JSONField(TextField):
    """Custom JSON field for Peewee."""
    def db_value(self, value):
        return json.dumps(value) if value is not None else None
    def python_value(self, value):
        return json.loads(value) if value is not None else None


class AuditLog(BaseModel):
    """Audit log for tracking system changes."""
    
    id = AutoField(help_text="Primary key")
    user = ForeignKeyField(User, backref='audit_logs', on_delete='SET NULL', null=True, help_text="User")
    action = CharField(max_length=255, help_text="Action performed")
    old_data = JSONField(null=True, help_text="Old data (JSON)")
    new_data = JSONField(null=True, help_text="New data (JSON)")
    ip_address = CharField(max_length=50, null=True, help_text="IP address")
    table_name = CharField(max_length=100, help_text="Table affected")
    created_at = DateTimeField(default=datetime.now, help_text="Timestamp")
    
    class Meta:
        table_name = 'audit_logs'
    
    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.action}"