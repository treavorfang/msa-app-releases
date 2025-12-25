"""AuthService - Authentication & Authorization Business Logic.

This service handles user authentication and uses DTOs for data transport.
"""

from typing import Tuple, Union, Optional
from datetime import datetime
from peewee import DoesNotExist, IntegrityError

from models.user import User
from models.role import Role
from interfaces.iauth_service import IAuthService
from utils.security.password_utils import hash_password, verify_password
from utils.validation.input_validator import InputValidator 
from dtos.user_dto import UserDTO


class AuthService(IAuthService):
    """Service class for authentication operations."""

    def __init__(self, user_repository, audit_service, role_service):
        """Initialize AuthService."""
        self.user_repository = user_repository
        self.audit_service = audit_service
        self.role_service = role_service

    def login_user(self, username: str, password: str, ip_address: str = None) -> Tuple[bool, Union[str, UserDTO]]:
        """Authenticate a user."""
        try:
            if not username or len(username.strip()) < 3:
                return False, "Username must be at least 3 characters"
                
            # Skip strict password validation on login (only verify correctness)
            # password_valid, password_msg = InputValidator.validate_password(password)
            # if not password_valid:
            #     return False, password_msg
            pass
            
            user = self.user_repository.get_by_username(username)
            
            if not user or not verify_password(user.password_hash, password):
                return False, "Invalid username or password"
            
            if not user.is_active:
                return False, "Account is disabled"

            user.last_login = datetime.now()
            user.save()

            # First user check
            first_user = User.select().order_by(User.id).first()
            if user == first_user:
                admin_role = self.role_service.get_role_by_name('admin')
                if not admin_role:
                    return False, "System configuration error - admin role missing"
                    
                if user.role != admin_role:
                    user.role = admin_role
                    user.save()
                
                self.audit_service.log_action(
                    user=user,
                    action="admin_login",
                    table_name="users",
                    ip_address=ip_address
                )
                return True, UserDTO.from_model(user, include_permissions=True)

            if not self.role_service.user_has_permission(user, "auth:login"):
                return False, "Account not authorized to login"
            
            self.audit_service.log_action(
                user=user,
                action="login",
                table_name="users",
                ip_address=ip_address
            )
            
            return True, UserDTO.from_model(user, include_permissions=True)
            
        except DoesNotExist:
            return False, "Invalid username or password"
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"DEBUG LOGIN ERROR: {error_trace}")
            return False, f"Login failed: {str(e)}"

    def register_user(self, username: str, email: str, password: str, current_user=None, ip_address: str = None) -> Tuple[bool, str]:
        """Register a new user account."""
        if not username or len(username.strip()) < 3:
            return False, "Username must be at least 3 characters"
            
        # Use local validation for registration
        email_valid, email_msg = InputValidator.validate_email(email)
        if not email_valid:
            return False, email_msg
            
        password_valid, password_msg = InputValidator.validate_password(password, is_local=True)
        if not password_valid:
            return False, password_msg

        if self.user_repository.username_exists(username):
            return False, "Username already exists"
            
        if self.user_repository.email_exists(email):
            return False, "Email already exists"

        is_first_user = User.select().count() == 0
        
        if is_first_user:
            role = self.role_service.get_role_by_name('admin')
            if not role:
                return False, "Admin role not found"
        else:
            role = self.role_service.get_role_by_name('user')
            if not role:
                role = Role.create(name='user', description='Regular user', is_system=True)

        try:
            user = User.create(
                username=username,
                email=email,
                full_name=username,
                password_hash=hash_password(password),
                is_active=True,
                role=role,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.audit_service.log_action(
                user=current_user if current_user else (user if is_first_user else None),
                action="user_register" if not is_first_user else "system_create_admin",
                table_name="users",
                new_data={
                    "username": username,
                    "email": email,
                    "role_id": role.id
                },
                ip_address=ip_address
            )
            
            return True, "Registration successful"
        except IntegrityError as e:
            return False, f"Registration failed: {str(e)}"

    def logout_user(self, user_id: int, ip_address: str = None) -> bool:
        """Log out a user."""
        try:
            user = self.user_repository.get_by_id(user_id)
            if user:
                self.audit_service.log_action(
                    user=user,
                    action="user_logout",
                    table_name="users",
                    ip_address=ip_address
                )
            return True
        except Exception as e:
            print(f"Error logging logout action: {str(e)}")
            return True

    def change_password(self, user_id: int, old_password: str, new_password: str, ip_address: str = None) -> Tuple[bool, str]:
        """Change a user's password."""
        try:
            user = self.user_repository.get_by_id(user_id)
            if not user:
                return False, "User not found"

            if not verify_password(user.password_hash, old_password):
                return False, "Current password is incorrect"
                
            if old_password == new_password:
                return False, "New password must be different"
                
            # Validate new password
            is_valid, msg = InputValidator.validate_password(new_password, is_local=True)
            if not is_valid:
                return False, msg
                
            user.password_hash = hash_password(new_password)
            user.updated_at = datetime.now()
            user.save()
            
            self.audit_service.log_action(
                user=user,
                action="password_change",
                table_name="users",
                old_data={"password_updated_at": user.updated_at},
                ip_address=ip_address
            )
            return True, "Password changed successfully"
        except Exception as e:
            return False, f"Password change failed: {str(e)}"
            
    def get_user(self, user_id: int) -> Optional[UserDTO]:
        """Get user by ID."""
        user = self.user_repository.get_by_id(user_id)
        return UserDTO.from_model(user, include_permissions=True) if user else None

    def reset_password(self, user_id: int, new_password: str, ip_address: str = None) -> Tuple[bool, str]:
        """Administratively reset password."""
        try:
            user = self.user_repository.get_by_id(user_id)
            if not user:
                return False, "User not found"
                
            # Validate new password
            is_valid, msg = InputValidator.validate_password(new_password, is_local=True)
            if not is_valid:
                return False, msg
                
            user.password_hash = hash_password(new_password)
            user.updated_at = datetime.now()
            user.save()
            
            self.audit_service.log_action(
                user=user,
                action="password_reset",
                table_name="users",
                ip_address=ip_address
            )
            return True, "Password reset successful"
        except Exception as e:
            return False, f"Password reset failed: {str(e)}"