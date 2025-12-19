"""
RolePermission Model - Role-Permission Junction Table.

Maps the many-to-many relationship between roles and permissions in the RBAC system.
Each record represents a permission granted to a role.

Features:
    - Composite primary key (role, permission)
    - Cascade deletion when role or permission is deleted
    - Efficient permission lookups

Example:
    >>> # Grant permission to role
    >>> RolePermission.create(
    ...     role=admin_role,
    ...     permission=create_users_perm
    ... )
    
    >>> # Get all permissions for a role
    >>> perms = RolePermission.select().where(
    ...     RolePermission.role == admin_role
    ... )

Database Schema:
    Table: role_permissions
    Columns:
        - role_id: Foreign key to Role (part of composite PK)
        - permission_id: Foreign key to Permission (part of composite PK)
    
    Primary Key: (role_id, permission_id)

Relationships:
    - role: Many-to-One (RolePermission -> Role)
    - permission: Many-to-One (RolePermission -> Permission)

See Also:
    - models.role.Role: Roles that have permissions
    - models.permission.Permission: Permissions granted to roles
"""

from peewee import ForeignKeyField, CompositeKey
from models.base_model import BaseModel
from models.role import Role
from models.permission import Permission


class RolePermission(BaseModel):
    """
    Junction table for Role-Permission many-to-many relationship.
    
    Attributes:
        role (Role): Role being granted permission
        permission (Permission): Permission being granted
    """
    
    role = ForeignKeyField(
        Role,
        backref='permissions',
        on_delete='CASCADE',
        help_text="Role being granted the permission"
    )
    
    permission = ForeignKeyField(
        Permission,
        backref='roles',
        on_delete='CASCADE',
        help_text="Permission being granted to the role"
    )
    
    class Meta:
        """Model metadata."""
        primary_key = CompositeKey('role', 'permission')
        table_name = 'role_permissions'
        indexes = (
            (('role', 'permission'), True),  # Unique composite
        )
    
    def __str__(self):
        """String representation."""
        return f"{self.role.name} -> {self.permission.code}"
    
    def __repr__(self):
        """Developer-friendly representation."""
        return f'<RolePermission role="{self.role.name}" permission="{self.permission.code}">'