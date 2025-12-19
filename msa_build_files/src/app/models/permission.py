"""
Permission Model - Granular Access Control.

Defines individual permissions for fine-grained access control in the RBAC system.
Permissions represent specific actions or features users can access.

Features:
    - Unique permission codes (e.g., "users:create", "tickets:view")
    - Categorized permissions for organization
    - Many-to-many relationship with roles
    - Descriptive names and descriptions

Example:
    >>> # Create permission
    >>> perm = Permission.create(
    ...     code="tickets:create",
    ...     name="Create Tickets",
    ...     category="Tickets",
    ...     description="Ability to create new repair tickets"
    ... )

Database Schema:
    Table: permissions
    Columns:
        - id: Primary key
        - code: Unique permission code (max 50 chars)
        - name: Human-readable name (max 100 chars)
        - category: Permission category (max 50 chars)
        - description: Detailed description

Relationships:
    - role_permissions: One-to-Many (Permission -> RolePermission)
    - roles: Many-to-Many (Permission <-> Role) via RolePermission

See Also:
    - models.role.Role: Roles that have permissions
    - models.role_permission.RolePermission: Permission assignments
"""

from peewee import AutoField, CharField, TextField
from models.base_model import BaseModel


class Permission(BaseModel):
    """
    Permission model for RBAC system.
    
    Attributes:
        id (int): Primary key
        code (str): Unique permission code
        name (str): Human-readable name
        category (str): Permission category
        description (str): Detailed description
    """
    
    id = AutoField(help_text="Primary key")
    
    code = CharField(
        max_length=50,
        unique=True,
        help_text="Unique permission code (e.g., 'users:create')"
    )
    
    name = CharField(
        max_length=100,
        null=True,
        help_text="Human-readable permission name"
    )
    
    category = CharField(
        max_length=50,
        null=True,
        help_text="Permission category for organization"
    )
    
    description = TextField(
        null=True,
        help_text="Detailed description of what this permission allows"
    )
    
    class Meta:
        """Model metadata."""
        table_name = 'permissions'
        indexes = (
            (('code',), True),  # Unique index
            (('category',), False),
        )
    
    def __str__(self):
        """String representation."""
        return self.name or self.code
    
    def __repr__(self):
        """Developer-friendly representation."""
        return f'<Permission code="{self.code}">'