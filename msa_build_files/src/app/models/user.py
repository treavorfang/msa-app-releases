"""
User Model - System User Management.

This module defines the User model which represents all system users including
administrators, staff, technicians, and other personnel who interact with the system.

Features:
    - Username and email-based authentication
    - Password hashing for security
    - Role-based access control (RBAC)
    - Branch association for multi-location support
    - Active/inactive status management
    - Last login tracking
    - Automatic timestamp management

Security:
    - Passwords are stored as bcrypt hashes
    - Never store plain text passwords
    - Email and username are unique
    - Active status for account management

Example:
    >>> # Create a new user
    >>> from utils.security.password_utils import hash_password
    >>> user = User.create(
    ...     username="john.doe",
    ...     full_name="John Doe",
    ...     email="john@example.com",
    ...     password_hash=hash_password("secure_password"),
    ...     role=admin_role,
    ...     branch=main_branch
    ... )
    
    >>> # Check if user is active
    >>> if user.is_active:
    ...     print("User can login")
    
    >>> # Update last login
    >>> user.last_login = datetime.now()
    >>> user.save()

Database Schema:
    Table: users
    
    Columns:
        - id: Primary key (auto-increment)
        - username: Unique username (max 50 chars)
        - full_name: User's full name (max 100 chars)
        - email: Unique email address (max 100 chars)
        - password_hash: Bcrypt password hash (255 chars)
        - is_active: Account active status
        - branch_id: Foreign key to Branch (optional)
        - role_id: Foreign key to Role (optional)
        - last_login: Last successful login timestamp
        - created_at: Account creation timestamp
        - updated_at: Last update timestamp
    
    Indexes:
        - UNIQUE (username)
        - UNIQUE (email)
        - INDEX (is_active)
        - INDEX (branch_id)
        - INDEX (role_id)

Relationships:
    - role: Many-to-One (User -> Role)
    - branch: Many-to-One (User -> Branch)
    - tickets_opened: One-to-Many (User -> Ticket) [backref]
    - tickets_approved: One-to-Many (User -> Ticket) [backref]
    - deleted_categories: One-to-Many (User -> Category) [backref]
    - audit_logs: One-to-Many (User -> AuditLog) [backref]

See Also:
    - models.role.Role: User roles and permissions
    - models.branch.Branch: Branch/location assignment
    - utils.security.password_utils: Password hashing utilities
    - services.auth_service.AuthService: Authentication logic
"""

from datetime import datetime
from peewee import (
    AutoField,
    CharField,
    BooleanField,
    ForeignKeyField,
    DateTimeField
)

from models.base_model import BaseModel
from models.role import Role
from models.branch import Branch


class User(BaseModel):
    """
    User model for system authentication and authorization.
    
    Represents all users in the system with role-based access control,
    branch association, and security features.
    
    Attributes:
        id (int): Primary key
        username (str): Unique username (max 50 chars)
        full_name (str): User's full name (max 100 chars)
        email (str): Unique email address (max 100 chars)
        password_hash (str): Bcrypt password hash (255 chars)
        is_active (bool): Whether account is active
        branch (Branch): Associated branch/location
        role (Role): User's role for permissions
        last_login (datetime): Last successful login time
        created_at (datetime): When account was created
        updated_at (datetime): When account was last updated
    
    Security Notes:
        - Always use password_utils.hash_password() for passwords
        - Never store plain text passwords
        - Check is_active before allowing login
        - Validate email format before saving
    
    Example:
        >>> user = User.create(
        ...     username="admin",
        ...     full_name="System Admin",
        ...     email="admin@example.com",
        ...     password_hash=hash_password("password"),
        ...     role=admin_role
        ... )
        >>> print(user.has_permission("users:create"))
    """
    
    # ==================== Primary Key ====================
    
    id = AutoField(
        help_text="Primary key, auto-incremented"
    )
    
    # ==================== Authentication ====================
    
    username = CharField(
        max_length=50,
        unique=True,
        help_text="Unique username for login (max 50 chars)"
    )
    
    password_hash = CharField(
        max_length=255,
        help_text="Bcrypt password hash (never store plain text)"
    )
    
    email = CharField(
        max_length=100,
        unique=True,
        help_text="Unique email address (max 100 chars)"
    )
    
    # ==================== Profile ====================
    
    full_name = CharField(
        max_length=100,
        help_text="User's full name (max 100 chars)"
    )
    
    # ==================== Relationships ====================
    
    role = ForeignKeyField(
        Role,
        backref='users',
        on_delete='SET NULL',
        null=True,
        help_text="User's role for permission management"
    )
    
    branch = ForeignKeyField(
        Branch,
        backref='users',
        on_delete='SET NULL',
        null=True,
        help_text="Associated branch/location"
    )
    
    # ==================== Status ====================
    
    is_active = BooleanField(
        default=True,
        help_text="Whether this account is active and can login"
    )
    
    # ==================== Timestamps ====================
    
    last_login = DateTimeField(
        null=True,
        help_text="When user last successfully logged in"
    )
    
    created_at = DateTimeField(
        default=datetime.now,
        help_text="When this account was created"
    )
    
    updated_at = DateTimeField(
        default=datetime.now,
        help_text="When this account was last updated"
    )
    
    # ==================== Meta Configuration ====================
    
    class Meta:
        """Model metadata and database configuration."""
        table_name = 'users'
        indexes = (
            (('username',), True),  # Unique index
            (('email',), True),     # Unique index
            (('is_active',), False),
            (('branch',), False),
            (('role',), False),
        )
    
    # ==================== Model Methods ====================
    
    def save(self, *args, **kwargs):
        """
        Save user with automatic timestamp update.
        
        Returns:
            int: Number of rows modified
        """
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
    def __str__(self):
        """String representation showing username and full name."""
        return f"{self.username} ({self.full_name})"
    
    def __repr__(self):
        """Developer-friendly representation."""
        return f'<User id={self.id} username="{self.username}" email="{self.email}">'
    
    # ==================== Helper Methods ====================
    
    def has_permission(self, permission_code: str) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            permission_code: Permission code to check (e.g., "users:create")
        
        Returns:
            bool: True if user has the permission
        
        Example:
            >>> if user.has_permission("tickets:create"):
            ...     print("Can create tickets")
        """
        if not self.role:
            return False
        
        # Get role permissions
        from models.role_permission import RolePermission
        from models.permission import Permission
        
        permission_exists = (
            RolePermission
            .select()
            .join(Permission)
            .where(
                (RolePermission.role == self.role) &
                (Permission.code == permission_code)
            )
            .exists()
        )
        
        return permission_exists
    
    def get_permissions(self) -> list:
        """
        Get all permissions for this user.
        
        Returns:
            list[Permission]: List of Permission objects
        
        Example:
            >>> perms = user.get_permissions()
            >>> print([p.code for p in perms])
            ['users:view', 'tickets:create', ...]
        """
        if not self.role:
            return []
        
        from models.role_permission import RolePermission
        from models.permission import Permission
        
        permissions = (
            Permission
            .select()
            .join(RolePermission)
            .where(RolePermission.role == self.role)
        )
        
        return list(permissions)
    
    def update_last_login(self):
        """
        Update last login timestamp to now.
        
        Call this after successful authentication.
        
        Example:
            >>> user.update_last_login()
        """
        self.last_login = datetime.now()
        self.save()
    
    def deactivate(self):
        """
        Deactivate this user account.
        
        Prevents user from logging in without deleting the account.
        
        Example:
            >>> user.deactivate()
            >>> assert not user.is_active
        """
        self.is_active = False
        self.save()
    
    def activate(self):
        """
        Activate this user account.
        
        Allows user to login again.
        
        Example:
            >>> user.activate()
            >>> assert user.is_active
        """
        self.is_active = True
        self.save()
    
    @classmethod
    def get_by_username(cls, username: str):
        """
        Get user by username.
        
        Args:
            username: Username to search for
        
        Returns:
            User or None if not found
        
        Example:
            >>> user = User.get_by_username("admin")
        """
        try:
            return cls.get(cls.username == username)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_by_email(cls, email: str):
        """
        Get user by email.
        
        Args:
            email: Email to search for
        
        Returns:
            User or None if not found
        
        Example:
            >>> user = User.get_by_email("admin@example.com")
        """
        try:
            return cls.get(cls.email == email)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_active_users(cls):
        """
        Get all active users.
        
        Returns:
            peewee.ModelSelect: Query for active users
        
        Example:
            >>> active = User.get_active_users()
            >>> print(f"Active users: {active.count()}")
        """
        return cls.select().where(cls.is_active == True)