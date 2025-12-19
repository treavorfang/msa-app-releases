"""
Role Model - Role-Based Access Control (RBAC).

Defines user roles for permission management and access control.
Roles group permissions together for easier user management.

Features:
    - Named roles (e.g., Admin, Technician, Manager)
    - Many-to-many relationship with permissions
    - Role descriptions for clarity
    - Timestamp tracking

Example:
    >>> # Create a role
    >>> admin_role = Role.create(
    ...     name="Administrator",
    ...     description="Full system access"
    ... )
    
    >>> # Assign permissions to role
    >>> from models.role_permission import RolePermission
    >>> RolePermission.create(role=admin_role, permission=perm)
    
    >>> # Get all users with this role
    >>> admins = admin_role.users

Database Schema:
    Table: roles
    Columns:
        - id: Primary key
        - name: Unique role name (max 50 chars)
        - description: Role description
        - created_at: Creation timestamp

Relationships:
    - users: One-to-Many (Role -> User) [backref]
    - role_permissions: One-to-Many (Role -> RolePermission)
    - permissions: Many-to-Many (Role <-> Permission) via RolePermission

See Also:
    - models.permission.Permission: Individual permissions
    - models.role_permission.RolePermission: Role-permission mapping
    - models.user.User: Users assigned to roles
"""

from datetime import datetime
from peewee import AutoField, CharField, TextField, DateTimeField
from models.base_model import BaseModel


class Role(BaseModel):
    """
    Role model for RBAC system.
    
    Attributes:
        id (int): Primary key
        name (str): Unique role name (max 50 chars)
        description (str): Role description
        created_at (datetime): When role was created
    """
    
    id = AutoField(help_text="Primary key")
    
    name = CharField(
        max_length=50,
        unique=True,
        help_text="Unique role name (e.g., 'Administrator')"
    )
    
    description = TextField(
        null=True,
        help_text="Description of role responsibilities"
    )
    
    created_at = DateTimeField(
        default=datetime.now,
        help_text="When this role was created"
    )
    
    class Meta:
        """Model metadata."""
        table_name = 'roles'
        indexes = (
            (('name',), True),  # Unique index
        )
    
    def __str__(self):
        """String representation."""
        return self.name
    
    def __repr__(self):
        """Developer-friendly representation."""
        return f'<Role id={self.id} name="{self.name}">'
    
    def get_permissions(self):
        """
        Get all permissions for this role.
        
        Returns:
            list[Permission]: List of permissions
        """
        from models.role_permission import RolePermission
        from models.permission import Permission
        
        return list(
            Permission
            .select()
            .join(RolePermission)
            .where(RolePermission.role == self)
        )
    
    def has_permission(self, permission_code: str) -> bool:
        """
        Check if role has a specific permission.
        
        Args:
            permission_code: Permission code to check
        
        Returns:
            bool: True if role has permission
        """
        from models.role_permission import RolePermission
        from models.permission import Permission
        
        return (
            RolePermission
            .select()
            .join(Permission)
            .where(
                (RolePermission.role == self) &
                (Permission.code == permission_code)
            )
            .exists()
        )