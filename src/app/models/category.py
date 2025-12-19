"""
Category Model - Part Categorization System.

This module defines the Category model which provides hierarchical organization
for parts and inventory items. Categories support parent-child relationships
for multi-level classification and include default markup percentages for pricing.

Features:
    - Hierarchical category structure (parent-child relationships)
    - Default markup percentage for pricing
    - Soft delete support (deleted_at, deleted_by)
    - Automatic timestamp management
    - Active/inactive status tracking

Example:
    >>> # Create a parent category
    >>> electronics = Category.create(
    ...     name="Electronics",
    ...     description="Electronic parts and components",
    ...     default_markup_percentage=25.0
    ... )
    
    >>> # Create a child category
    >>> phones = Category.create(
    ...     name="Mobile Phones",
    ...     parent=electronics,
    ...     default_markup_percentage=30.0
    ... )
    
    >>> # Get all children of a category
    >>> children = electronics.children
    
    >>> # Get active categories
    >>> active = Category.select().where(
    ...     Category.is_active == True,
    ...     Category.deleted_at.is_null()
    ... )

Database Schema:
    Table: categories
    
    Columns:
        - id: Primary key (auto-increment)
        - name: Category name (unique, max 50 chars)
        - description: Optional detailed description
        - parent_id: Self-referencing foreign key for hierarchy
        - default_markup_percentage: Default pricing markup (0.00-999.99)
        - is_active: Active status flag
        - created_at: Creation timestamp
        - updated_at: Last update timestamp
        - deleted_at: Soft delete timestamp (NULL if not deleted)
        - deleted_by_id: User who deleted the category
    
    Indexes:
        - PRIMARY KEY (id)
        - UNIQUE (name)
        - INDEX (parent_id)
        - INDEX (is_active)
        - INDEX (deleted_at)

Relationships:
    - parent: Self-referencing (Category -> Category)
    - children: Reverse relationship (backref)
    - deleted_by: Many-to-One (Category -> User)
    - parts: One-to-Many (Category -> Part) [defined in Part model]

See Also:
    - models.part.Part: Parts that belong to categories
    - models.base_model.BaseModel: Base model with common functionality
    - models.user.User: User who performs soft deletes
"""

from datetime import datetime
from peewee import (
    AutoField,
    CharField,
    TextField,
    ForeignKeyField,
    DecimalField,
    BooleanField,
    DateTimeField
)

from models.base_model import BaseModel
from models.user import User


class Category(BaseModel):
    """
    Category model for hierarchical part organization.
    
    Provides a flexible categorization system with support for:
    - Multi-level hierarchies (parent-child relationships)
    - Default pricing markup percentages
    - Soft deletion with audit trail
    - Active/inactive status management
    
    Attributes:
        id (int): Primary key, auto-incremented
        name (str): Unique category name (max 50 characters)
        description (str, optional): Detailed category description
        parent (Category, optional): Parent category for hierarchy
        default_markup_percentage (Decimal): Default markup for pricing (0.00-999.99%)
        is_active (bool): Whether category is active (default: True)
        created_at (datetime): When category was created
        updated_at (datetime): When category was last updated
        deleted_at (datetime, optional): When category was soft deleted
        deleted_by (User, optional): User who deleted the category
    
    Relationships:
        children (list[Category]): Child categories (backref from parent)
        parts (list[Part]): Parts in this category (backref from Part model)
        deleted_categories (list[Category]): Categories deleted by user (backref)
    
    Meta:
        table_name: 'categories'
    
    Example:
        >>> # Create a category
        >>> category = Category.create(
        ...     name="Screens",
        ...     description="Display screens and LCDs",
        ...     default_markup_percentage=35.0
        ... )
        
        >>> # Update category
        >>> category.description = "Updated description"
        >>> category.save()  # updated_at is automatically set
        
        >>> # Soft delete
        >>> category.deleted_at = datetime.now()
        >>> category.deleted_by = current_user
        >>> category.save()
    """
    
    # ==================== Primary Key ====================
    
    id = AutoField(
        help_text="Primary key, auto-incremented"
    )
    
    # ==================== Core Fields ====================
    
    name = CharField(
        max_length=50,
        unique=True,
        help_text="Unique category name (max 50 characters)"
    )
    
    description = TextField(
        null=True,
        help_text="Optional detailed description of the category"
    )
    
    # ==================== Hierarchy ====================
    
    parent = ForeignKeyField(
        'self',
        backref='children',
        null=True,
        on_delete='SET NULL',
        help_text="Parent category for hierarchical organization"
    )
    
    # ==================== Pricing ====================
    
    default_markup_percentage = DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        help_text="Default markup percentage for parts in this category (0.00-999.99)"
    )
    
    # ==================== Status ====================
    
    is_active = BooleanField(
        default=True,
        help_text="Whether this category is active and available for use"
    )
    
    # ==================== Timestamps ====================
    
    created_at = DateTimeField(
        default=datetime.now,
        help_text="When this category was created"
    )
    
    updated_at = DateTimeField(
        default=datetime.now,
        help_text="When this category was last updated"
    )
    
    # ==================== Soft Delete ====================
    
    deleted_at = DateTimeField(
        null=True,
        help_text="When this category was soft deleted (NULL if not deleted)"
    )
    
    deleted_by = ForeignKeyField(
        User,
        backref='deleted_categories',
        null=True,
        on_delete='SET NULL',
        help_text="User who soft deleted this category"
    )
    
    # ==================== Meta Configuration ====================
    
    class Meta:
        """Model metadata and database configuration."""
        table_name = 'categories'
        indexes = (
            # Composite index for active, non-deleted categories
            (('is_active', 'deleted_at'), False),
        )
    
    # ==================== Model Methods ====================
    
    def save(self, *args, **kwargs):
        """
        Save the category with automatic timestamp update.
        
        Automatically updates the updated_at field to the current time
        whenever the model is saved.
        
        Args:
            *args: Positional arguments passed to parent save()
            **kwargs: Keyword arguments passed to parent save()
        
        Returns:
            int: Number of rows modified (typically 1)
        
        Example:
            >>> category.name = "Updated Name"
            >>> category.save()  # updated_at is automatically set
        """
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
    def __str__(self):
        """
        String representation of the category.
        
        Returns:
            str: Category name
        
        Example:
            >>> category = Category.get_by_id(1)
            >>> print(category)
            'Electronics'
        """
        return self.name
    
    def __repr__(self):
        """
        Developer-friendly representation of the category.
        
        Returns:
            str: Category representation with ID and name
        
        Example:
            >>> category = Category.get_by_id(1)
            >>> repr(category)
            '<Category id=1 name="Electronics">'
        """
        return f'<Category id={self.id} name="{self.name}">'
    
    # ==================== Helper Methods ====================
    
    def get_full_path(self):
        """
        Get the full hierarchical path of this category.
        
        Returns the category path from root to this category,
        separated by ' > '.
        
        Returns:
            str: Full category path (e.g., "Electronics > Mobile Phones > Screens")
        
        Example:
            >>> screens = Category.get(Category.name == "Screens")
            >>> screens.get_full_path()
            'Electronics > Mobile Phones > Screens'
        """
        path = [self.name]
        current = self.parent
        
        while current:
            path.insert(0, current.name)
            current = current.parent
        
        return ' > '.join(path)
    
    def get_all_children(self, include_inactive=False):
        """
        Get all descendant categories (recursive).
        
        Returns all child categories and their children recursively.
        
        Args:
            include_inactive (bool): Whether to include inactive categories
        
        Returns:
            list[Category]: All descendant categories
        
        Example:
            >>> electronics = Category.get(Category.name == "Electronics")
            >>> all_children = electronics.get_all_children()
            >>> print([c.name for c in all_children])
            ['Mobile Phones', 'Screens', 'Batteries', ...]
        """
        result = []
        
        query = self.children
        if not include_inactive:
            query = query.where(Category.is_active == True)
        
        for child in query:
            result.append(child)
            result.extend(child.get_all_children(include_inactive))
        
        return result
    
    @classmethod
    def get_root_categories(cls, include_inactive=False):
        """
        Get all root (top-level) categories.
        
        Returns categories that have no parent.
        
        Args:
            include_inactive (bool): Whether to include inactive categories
        
        Returns:
            peewee.ModelSelect: Query for root categories
        
        Example:
            >>> roots = Category.get_root_categories()
            >>> print([c.name for c in roots])
            ['Electronics', 'Accessories', 'Services']
        """
        query = cls.select().where(
            cls.parent.is_null(),
            cls.deleted_at.is_null()
        )
        
        if not include_inactive:
            query = query.where(cls.is_active == True)
        
        return query