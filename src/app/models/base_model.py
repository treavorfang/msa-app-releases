"""BaseModel - Base Class for All Models.

Provides common database configuration for all models in the application.
All models inherit from this base class to use the configured database connection.

Example:
    >>> from models.base_model import BaseModel
    >>> from peewee import CharField
    >>> 
    >>> class MyModel(BaseModel):
    ...     name = CharField()
    ...     
    ...     class Meta:
    ...         table_name = 'my_table'
"""

from peewee import Model
from config.database import db


class BaseModel(Model):
    """
    Base model class for all database models.
    
    Provides database configuration that all models inherit.
    All models in the application should extend this class.
    """
    
    class Meta:
        """Database configuration."""
        database = db