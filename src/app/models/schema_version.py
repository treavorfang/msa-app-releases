"""SchemaVersion Model - Database Migration Tracking.

Tracks applied database schema migrations to ensure database structure
is up-to-date and migrations are applied in the correct order.

Example:
    >>> # Record a migration
    >>> SchemaVersion.create(
    ...     version=1,
    ...     name="initial_schema"
    ... )
    
    >>> # Check current version
    >>> latest = SchemaVersion.select().order_by(
    ...     SchemaVersion.version.desc()
    ... ).first()
    >>> print(f"Current schema version: {latest.version}")
"""

from datetime import datetime
from peewee import IntegerField, CharField, DateTimeField
from models.base_model import BaseModel


class SchemaVersion(BaseModel):
    """
    Schema version tracking for database migrations.
    
    Attributes:
        version (int): Migration version number (unique)
        name (str): Migration name/description
        applied_at (datetime): When migration was applied
    """
    
    version = IntegerField(
        unique=True,
        help_text="Migration version number"
    )
    
    name = CharField(
        help_text="Migration name/description"
    )
    
    applied_at = DateTimeField(
        default=datetime.now,
        help_text="When migration was applied"
    )
    
    class Meta:
        """Model metadata."""
        table_name = 'schema_versions'
    
    def __str__(self):
        """String representation."""
        return f"v{self.version}: {self.name}"
    
    def __repr__(self):
        """Developer-friendly representation."""
        return f'<SchemaVersion version={self.version} name="{self.name}">'
