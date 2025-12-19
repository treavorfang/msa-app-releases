"""Role Repository - Role Data Access Layer.

This repository handles all database operations for Role entities.
Manages roles and their associated permissions for RBAC.
"""

from typing import List, Optional
from peewee import IntegrityError
from models.role import Role
from models.permission import Permission


class RoleRepository:
    """Repository for Role data access operations."""
    
    def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        try:
            return Role.get(Role.name == name)
        except Role.DoesNotExist:
            return None
    
    def create_role(self, name: str, description: str = None) -> Optional[Role]:
        """Create a new role."""
        try:
            return Role.create(name=name, description=description)
        except IntegrityError:
            return None
    
    def add_permission_to_role(self, role: Role, permission_name: str, permission_code: str) -> Optional[Permission]:
        """Add a permission to a role."""
        try:
            return Permission.create(
                role=role,
                name=permission_name,
                code=permission_code
            )
        except IntegrityError:
            return None
    
    def get_user_roles(self, user) -> List[Role]:
        """Get all roles for a user.
        
        Note: This would require a many-to-many relationship between User and Role.
        For simplicity, returns an empty list.
        """
        return []
    
    def get_role_permissions(self, role: Role) -> List[Permission]:
        """Get all permissions for a role."""
        return list(role.permissions)