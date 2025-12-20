"""User DTO - Data Transfer Object."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class UserDTO:
    """Data Transfer Object for User."""
    
    id: Optional[int] = None
    username: str = ""
    full_name: str = ""
    email: str = ""
    is_active: bool = True
    branch_id: Optional[int] = None
    role_id: Optional[int] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    # Flattened
    role_name: Optional[str] = None
    branch_name: Optional[str] = None
    
    # Permissions (computed)
    permissions: List[str] = field(default_factory=list)

    @classmethod
    def from_model(cls, user, include_permissions: bool = False) -> 'UserDTO':
        """Convert model to DTO."""
        dto = cls(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            branch_id=user.branch_id if user.branch else None,
            role_id=user.role_id if user.role else None,
            last_login=user.last_login,
            created_at=user.created_at,
            role_name=user.role.name if user.role else None,
            branch_name=user.branch.name if user.branch else None
        )
        if include_permissions:
            # Assumes user.get_permissions() returns list of Permission models
            perms = user.get_permissions()
            dto.permissions = [p.code for p in perms]
        return dto
    
    def has_permission(self, permission_code: str) -> bool:
        """Check if user has specific permission."""
        return permission_code in self.permissions
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'user_id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'email': self.email,
            'is_active': self.is_active,
            'branch_id': self.branch_id,
            'role_id': self.role_id,
            'last_login': self.last_login.isoformat() if hasattr(self.last_login, 'isoformat') else self.last_login,
            'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else self.created_at
        }
