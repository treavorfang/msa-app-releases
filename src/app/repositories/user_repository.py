"""User Repository - User Data Access Layer.

This repository handles all database operations for User entities.
Provides methods for user authentication, CRUD operations, and user management.
"""

from datetime import datetime
from typing import Optional, Tuple, List
from peewee import IntegrityError
from models.user import User


class UserRepository:
    """Repository for User data access operations."""
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            return User.get_by_id(user_id)
        except User.DoesNotExist:
            return None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            return User.get(User.username == username)
        except User.DoesNotExist:
            return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        try:
            return User.get(User.email == email)
        except User.DoesNotExist:
            return None
    
    def username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        return self.get_by_username(username) is not None
    
    def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        return self.get_by_email(email) is not None
    
    def create_user(self, username: str, email: str, password: str) -> Tuple[Optional[User], bool]:
        """Create a new user with hashed password."""
        try:
            user = User.create(
                username=username,
                email=email,
                full_name=username,  # Default to username
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            user.set_password(password)
            user.save()
            return user, True
        except IntegrityError:
            return None, False
    
    def update_user(self, user: User) -> bool:
        """Update user and set updated_at timestamp."""
        try:
            user.updated_at = datetime.now()
            user.save()
            return True
        except IntegrityError:
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user by ID."""
        try:
            user = User.get_by_id(user_id)
            user.delete_instance()
            return True
        except User.DoesNotExist:
            return False
    
    def list_all(self) -> List[User]:
        """Get all users."""
        return list(User.select())