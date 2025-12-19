# src/app/interfaces/irole_service.py
from abc import ABC, abstractmethod
from typing import List, Optional
from models.user import User
from models.role import Role
from models.permission import Permission

class IRoleService(ABC):
    @abstractmethod
    def user_has_role(self, user: User, role_name: str) -> bool:
        """Check if user has a specific role"""
        pass

    @abstractmethod
    def assign_role_to_user(self, user: User, role_name: str, current_user: User) -> bool:
        pass
        
    @abstractmethod
    def add_permission_to_role(self, role: Role, permission_code: str, current_user: User) -> bool:
        pass
        
    @abstractmethod
    def remove_permission_from_role(self, role: Role, permission_code: str, current_user: User) -> bool:
        pass
        
    @abstractmethod
    def user_has_permission(self, user: User, permission_code: str) -> bool:
        pass
        
    @abstractmethod
    def get_role_permissions(self, role: Role) -> List[Permission]:
        pass

    @abstractmethod
    def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get a role by its name"""
        pass