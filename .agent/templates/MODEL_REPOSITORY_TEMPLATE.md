# Phase 2: Data Layer - Pattern & Template

## ✅ Completed Sample Files (2/6)

### 1. Category Model ✅

- **Type**: Simple model with hierarchy
- **Pattern**: Basic fields, helper methods, relationships
- **Location**: `/models/category.py`

### 2. Ticket Model ✅

- **Type**: Complex model with business logic
- **Pattern**: Multiple relationships, status workflow, financial tracking
- **Location**: `/models/ticket.py`

---

## 📋 Established Pattern

### Module Structure (Standard Template)

```python
"""
[Model Name] Model - [Brief Description].

This module defines the [Model] model which [purpose].

Features:
    - [Feature 1]
    - [Feature 2]
    - [Feature 3]

Example:
    >>> # Create example
    >>> obj = Model.create(...)

    >>> # Query example
    >>> results = Model.select().where(...)

Database Schema:
    Table: [table_name]

    Columns:
        - id: Primary key
        - [field]: [description]

    Indexes:
        - [index description]

Relationships:
    - [relationship]: [type] ([Model] -> [Related Model])

See Also:
    - [Related models]
    - [Related services]
"""

from datetime import datetime
from peewee import (
    AutoField,
    CharField,
    # ... other field types
)

from models.base_model import BaseModel
# ... other imports


class ModelName(BaseModel):
    """
    [Model] model for [purpose].

    [Detailed description of what this model represents]

    Attributes:
        id (int): Primary key
        [field] ([type]): [description]

    Relationships:
        [relationship] ([type]): [description]

    Example:
        >>> obj = ModelName.create(...)
        >>> obj.save()
    """

    # ==================== Primary Key ====================

    id = AutoField(
        help_text="Primary key, auto-incremented"
    )

    # ==================== Core Fields ====================

    name = CharField(
        max_length=100,
        help_text="[Field description]"
    )

    # ==================== Relationships ====================

    # ... foreign keys

    # ==================== Status/Flags ====================

    # ... boolean fields

    # ==================== Timestamps ====================

    created_at = DateTimeField(
        default=datetime.now,
        help_text="When this record was created"
    )

    updated_at = DateTimeField(
        default=datetime.now,
        help_text="When this record was last updated"
    )

    # ==================== Soft Delete ====================

    deleted_at = DateTimeField(
        null=True,
        help_text="When this record was soft deleted"
    )

    # ==================== Meta Configuration ====================

    class Meta:
        """Model metadata and database configuration."""
        table_name = '[table_name]'
        indexes = (
            # Define indexes here
        )

    # ==================== Model Methods ====================

    def save(self, *args, **kwargs):
        """
        Save with automatic timestamp update.

        Returns:
            int: Number of rows modified
        """
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)

    def __str__(self):
        """String representation."""
        return self.name

    def __repr__(self):
        """Developer-friendly representation."""
        return f'<{self.__class__.__name__} id={self.id} name="{self.name}">'

    # ==================== Helper Methods ====================

    def custom_method(self):
        """
        [Method description].

        Returns:
            [type]: [description]

        Example:
            >>> obj.custom_method()
        """
        pass

    @classmethod
    def custom_class_method(cls):
        """
        [Class method description].

        Returns:
            [type]: [description]

        Example:
            >>> ModelName.custom_class_method()
        """
        pass
```

---

## 📋 Repository Pattern Template

```python
"""
[Model] Repository - Data Access Layer.

This module provides data access methods for [Model] entities.
Handles all database operations including CRUD, queries, and transactions.

Features:
    - CRUD operations
    - Filtering and searching
    - Pagination support
    - Transaction management
    - Query optimization

Example:
    >>> repo = ModelRepository()
    >>> obj = repo.create(name="Example")
    >>> results = repo.get_all(active_only=True)
    >>> obj = repo.get_by_id(1)
    >>> repo.update(obj, name="Updated")
    >>> repo.delete(obj)

See Also:
    - models.[model].[Model]: Model definition
    - services.[model]_service.[Model]Service: Business logic
"""

from typing import List, Optional
from peewee import DoesNotExist

from models.[model] import [Model]
from repositories.base_repository import BaseRepository


class [Model]Repository(BaseRepository):
    """
    Repository for [Model] data access.

    Provides optimized database operations for [Model] entities
    with support for filtering, pagination, and relationships.

    Attributes:
        model_class: The [Model] class

    Example:
        >>> repo = [Model]Repository()
        >>> obj = repo.create(name="Example")
        >>> all_items = repo.get_all()
    """

    def __init__(self):
        """Initialize repository with [Model] class."""
        super().__init__([Model])

    # ==================== CRUD Operations ====================

    def create(self, **kwargs) -> [Model]:
        """
        Create a new [model].

        Args:
            **kwargs: Field values for the new [model]

        Returns:
            [Model]: Created [model] instance

        Raises:
            IntegrityError: If unique constraint violated

        Example:
            >>> obj = repo.create(name="Example")
        """
        return self.model_class.create(**kwargs)

    def get_by_id(self, id: int) -> Optional[[Model]]:
        """
        Get [model] by ID.

        Args:
            id: [Model] ID

        Returns:
            [Model] or None if not found

        Example:
            >>> obj = repo.get_by_id(1)
        """
        try:
            return self.model_class.get_by_id(id)
        except DoesNotExist:
            return None

    def get_all(
        self,
        active_only: bool = True,
        include_deleted: bool = False
    ) -> List[[Model]]:
        """
        Get all [models].

        Args:
            active_only: Only return active records
            include_deleted: Include soft-deleted records

        Returns:
            List of [Model] instances

        Example:
            >>> all_items = repo.get_all()
            >>> active_items = repo.get_all(active_only=True)
        """
        query = self.model_class.select()

        if active_only and hasattr(self.model_class, 'is_active'):
            query = query.where(self.model_class.is_active == True)

        if not include_deleted and hasattr(self.model_class, 'deleted_at'):
            query = query.where(self.model_class.deleted_at.is_null())

        return list(query)

    def update(self, instance: [Model], **kwargs) -> [Model]:
        """
        Update [model] instance.

        Args:
            instance: [Model] instance to update
            **kwargs: Fields to update

        Returns:
            Updated [Model] instance

        Example:
            >>> obj = repo.update(obj, name="Updated")
        """
        for key, value in kwargs.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def delete(self, instance: [Model], soft: bool = True) -> bool:
        """
        Delete [model] instance.

        Args:
            instance: [Model] instance to delete
            soft: Use soft delete if True

        Returns:
            True if deleted successfully

        Example:
            >>> repo.delete(obj)  # Soft delete
            >>> repo.delete(obj, soft=False)  # Hard delete
        """
        if soft and hasattr(instance, 'deleted_at'):
            from datetime import datetime
            instance.deleted_at = datetime.now()
            instance.save()
        else:
            instance.delete_instance()
        return True

    # ==================== Query Methods ====================

    def search(self, query: str) -> List[[Model]]:
        """
        Search [models] by query string.

        Args:
            query: Search query

        Returns:
            List of matching [Model] instances

        Example:
            >>> results = repo.search("example")
        """
        # Implement search logic
        pass

    def filter_by(self, **filters) -> List[[Model]]:
        """
        Filter [models] by criteria.

        Args:
            **filters: Filter criteria

        Returns:
            List of filtered [Model] instances

        Example:
            >>> results = repo.filter_by(status="active")
        """
        query = self.model_class.select()

        for field, value in filters.items():
            if hasattr(self.model_class, field):
                query = query.where(
                    getattr(self.model_class, field) == value
                )

        return list(query)

    # ==================== Helper Methods ====================

    def exists(self, id: int) -> bool:
        """
        Check if [model] exists.

        Args:
            id: [Model] ID

        Returns:
            True if exists

        Example:
            >>> if repo.exists(1):
            ...     print("Exists")
        """
        return self.get_by_id(id) is not None

    def count(self, **filters) -> int:
        """
        Count [models] matching filters.

        Args:
            **filters: Filter criteria

        Returns:
            Count of matching records

        Example:
            >>> total = repo.count()
            >>> active = repo.count(is_active=True)
        """
        query = self.model_class.select()

        for field, value in filters.items():
            if hasattr(self.model_class, field):
                query = query.where(
                    getattr(self.model_class, field) == value
                )

        return query.count()
```

---

## 🎯 Quick Reference Checklist

### For Each Model File:

- [ ] Module docstring with features, examples, schema
- [ ] Class docstring with attributes
- [ ] Group fields by purpose (use section comments)
- [ ] Add help_text to all fields
- [ ] Implement `__str__()` and `__repr__()`
- [ ] Add helper methods for common operations
- [ ] Document Meta class
- [ ] Add usage examples in docstrings

### For Each Repository File:

- [ ] Module docstring with purpose and examples
- [ ] Class docstring
- [ ] Implement CRUD methods with docstrings
- [ ] Add query/filter methods
- [ ] Add helper methods (exists, count, etc.)
- [ ] Document all parameters and return values
- [ ] Add usage examples

---

## 📚 Documentation created and ready for you to apply to remaining files!

**Pattern established** ✅
**Templates created** ✅
**Examples provided** ✅

You can now apply this pattern to the remaining 32 models and 28 repositories!
