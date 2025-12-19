"""IAuthService - Interface for Authentication Service."""

from abc import ABC, abstractmethod
from typing import Tuple, Union, Optional
from dtos.user_dto import UserDTO

class IAuthService(ABC):
    """Interface for authentication services."""
    
    @abstractmethod
    def register_user(self, username: str, email: str, password: str, current_user=None, ip_address: str = None) -> Tuple[bool, str]:
        """
        Register a new user.
        Returns tuple of (success: bool, message: str)
        """
        pass
    
    @abstractmethod
    def login_user(self, username: str, password: str, ip_address: str = None) -> Tuple[bool, Union[str, UserDTO]]:
        """
        Authenticate a user.
        Returns tuple of (success: bool, result: str|UserDTO)
        """
        pass
    
    @abstractmethod
    def logout_user(self, user_id: int) -> bool:
        """Log out a user."""
        pass
    
    @abstractmethod
    def change_password(self, user_id: int, old_password: str, new_password: str, ip_address: str = None) -> Tuple[bool, str]:
        """Change user password."""
        pass
    
    @abstractmethod
    def get_user(self, user_id: int) -> Optional[UserDTO]:
        """Get user by ID."""
        pass