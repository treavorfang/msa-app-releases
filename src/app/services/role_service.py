"""RoleService - Role Based Access Control (RBAC) Logic.

This service manages roles, permissions, and user assignments.
It handles initialization of default system roles and runtime permission checks.
"""

from typing import List, Optional
from peewee import IntegrityError, DoesNotExist

from models.user import User
from models.role import Role
from models.permission import Permission
from models.role_permission import RolePermission
from interfaces.irole_service import IRoleService
from interfaces.iaudit_service import IAuditService


class RoleService(IRoleService):
    """Service class for RBAC operations."""
    
    _audit_service = None  # Class-level reference for static methods
    
    def __init__(self, audit_service: IAuditService):
        """Initialize RoleService.
        
        Args:
            audit_service: Service for logging security events
        """
        if not audit_service:
            raise ValueError("audit_service is required")
        self.__class__._audit_service = audit_service
        self.audit_service = audit_service
    
    @classmethod
    def create_default_roles(cls, audit_service: IAuditService) -> None:
        """Initialize system with default roles and permissions if they don't exist.
        
        This method defines the entire permission schema and default role capabilities.
        It should be run during system startup or migration.
        """
        service = audit_service or cls._audit_service
        if not service:
            raise ValueError("audit_service must be provided either through instance or parameter")

        # Define all available permissions in the system.
        # Format: (code, name, category, description)
        all_permissions = [
            # System / Admin
            ('admin:access', 'Admin Access', 'system', 'Access to admin dashboard'),
            ('settings:manage', 'Manage Settings', 'system', 'Configure system settings'),
            ('users:manage', 'Manage Users', 'users', 'Create and manage users'),
            ('roles:manage', 'Manage Roles', 'users', 'Manage roles and permissions'),
            ('audit:view', 'View Audit Logs', 'system', 'View system audit logs'),
            
            # Reports
            ('reports:view', 'View Reports', 'reports', 'View system reports'),
            ('reports:export', 'Export Reports', 'reports', 'Export reports to PDF/CSV'),
            ('reports:financial', 'Financial Reports', 'reports', 'View sensitive financial reports'),
            
            # Tickets
            ('tickets:view', 'View Tickets', 'tickets', 'View tickets list'),
            ('tickets:create', 'Create Tickets', 'tickets', 'Create new tickets'),
            ('tickets:edit', 'Edit Tickets', 'tickets', 'Edit existing tickets'),
            ('tickets:delete', 'Delete Tickets', 'tickets', 'Delete tickets'),
            ('tickets:assign', 'Assign Tickets', 'tickets', 'Assign tickets to technicians'),
            
            # Invoices
            ('invoices:view', 'View Invoices', 'invoices', 'View invoices'),
            ('invoices:create', 'Create Invoices', 'invoices', 'Create new invoices'),
            ('invoices:edit', 'Edit Invoices', 'invoices', 'Edit existing invoices'),
            ('invoices:delete', 'Delete Invoices', 'invoices', 'Delete invoices'),
            
            # Customers
            ('customers:view', 'View Customers', 'customers', 'View customer details'),
            ('customers:manage', 'Manage Customers', 'customers', 'Create and edit customers'),
            
            # Inventory
            ('inventory:view', 'View Inventory', 'inventory', 'View inventory levels'),
            ('inventory:manage', 'Manage Inventory', 'inventory', 'Add/Edit parts and stock'),
            
            # Technicians
            ('technicians:view', 'View Technicians', 'technicians', 'View technicians list'),
            ('technicians:manage', 'Manage Technicians', 'technicians', 'Add/Edit technicians'),
        ]

        # 1. Create all permissions
        for code, name, category, desc in all_permissions:
            try:
                # Use get_or_create to avoid duplicates
                perm, created = Permission.get_or_create(
                    code=code,
                    defaults={'description': desc}
                )
                if created:
                    service.log_action(user=None, action="system_create_perm", table_name="permissions", new_data={"code": code})
            except IntegrityError:
                pass  # Should be handled by get_or_create but safety first

        # 2. Define Roles and their Permission Codes
        roles_config = {
            'admin': {
                'desc': 'Administrator with full system access',
                'perms': [p[0] for p in all_permissions]  # All permissions
            },
            'manager': {
                'desc': 'Manager with oversight capabilities',
                'perms': [
                    'reports:view', 'reports:export', 'reports:financial',
                    'tickets:view', 'tickets:create', 'tickets:edit', 'tickets:assign',
                    'invoices:view', 'invoices:create', 'invoices:edit',
                    'customers:view', 'customers:manage',
                    'inventory:view', 'inventory:manage',
                    'technicians:view', 'technicians:manage',
                    'users:manage' # Managers can manage users usually (except admins)
                ]
            },
            'staff': {
                'desc': 'Front desk staff or standard user',
                'perms': [
                    'tickets:view', 'tickets:create', 'tickets:edit',
                    'invoices:view', 'invoices:create',
                    'customers:view', 'customers:manage',
                    'inventory:view'
                ]
            },
            'technician': {
                'desc': 'Repair technician',
                'perms': [
                    'tickets:view', 'tickets:edit', # View and update their tickets
                    'inventory:view'
                ]
            }
        }

        # 3. Create Roles and Assign Permissions
        for role_name, config in roles_config.items():
            role, created = Role.get_or_create(
                name=role_name,
                defaults={'description': config['desc']}
            )
            
            if created:
                service.log_action(user=None, action="system_create_role", table_name="roles", new_data={"name": role_name})
            
            # Assign permissions
            for perm_code in config['perms']:
                try:
                    perm = Permission.get(Permission.code == perm_code)
                    RolePermission.get_or_create(role=role, permission=perm)
                except Permission.DoesNotExist:
                    print(f"Warning: Permission {perm_code} not found for role {role_name}")

        # Ensure 'user' role exists for backward compatibility (map to staff or keep as minimal)
        Role.get_or_create(name='user', defaults={'description': 'Default user'})

    def user_has_role(self, user: User, role_name: str) -> bool:
        """Check if user has a specific role."""
        if not user or not user.role:
            return False
        return user.role.name.lower() == role_name.lower()

    def assign_role_to_user(self, user: User, role_name: str, current_user: User) -> bool:
        """Assign a role to a user and log the action."""
        try:
            role = Role.get(Role.name == role_name)
            old_role = user.role
            
            user.role = role
            user.save()
            
            self.audit_service.log_action(
                user=current_user,
                action="assign_role",
                table_name="users",
                old_data={"role_id": old_role.id if old_role else None},
                new_data={"role_id": role.id}
            )
            return True
        except (Role.DoesNotExist, IntegrityError):
            return False

    def add_permission_to_role(self, role: Role, permission_code: str, current_user: User) -> bool:
        """Grant a specific permission to a role."""
        try:
            permission = Permission.get(Permission.code == permission_code)
            RolePermission.create(role=role, permission=permission)
            
            self.audit_service.log_action(
                user=current_user,
                action="add_permission_to_role",
                table_name="role_permissions",
                new_data={
                    "role_id": role.id,
                    "permission_id": permission.id,
                    "permission_code": permission.code
                }
            )
            return True
        except (Permission.DoesNotExist, IntegrityError):
            return False

    def remove_permission_from_role(self, role: Role, permission_code: str, current_user: User) -> bool:
        """Revoke a permission from a role."""
        try:
            permission = Permission.get(Permission.code == permission_code)
            rp = RolePermission.get(
                (RolePermission.role == role) &
                (RolePermission.permission == permission)
            )
            
            self.audit_service.log_action(
                user=current_user,
                action="remove_permission_from_role",
                table_name="role_permissions",
                old_data={
                    "role_id": role.id,
                    "permission_id": permission.id,
                    "permission_code": permission.code
                }
            )
            
            rp.delete_instance()
            return True
        except (Permission.DoesNotExist, RolePermission.DoesNotExist):
            return False

    def user_has_permission(self, user: User, permission_code: str) -> bool:
        """Check if a user has a specific permission via their role."""
        if not user:
            return False
            
        role_to_check = None
        
        # Handle User Model (has .role relation)
        if hasattr(user, 'role') and user.role:
            role_to_check = user.role
        # Handle UserDTO (has .role_id)
        elif hasattr(user, 'role_id') and user.role_id:
            try:
                role_to_check = Role.get_by_id(user.role_id)
            except (Role.DoesNotExist, DoesNotExist):
                return False
        
        if not role_to_check:
            return False
            
        try:
            permission = Permission.get(Permission.code == permission_code)
            return RolePermission.select().where(
                (RolePermission.role == role_to_check) &
                (RolePermission.permission == permission)
            ).exists()
        except (Permission.DoesNotExist, RolePermission.DoesNotExist, DoesNotExist):
            return False

    def get_role_permissions(self, role: Role) -> List[Permission]:
        """Get all permissions assigned to a role."""
        return [rp.permission for rp in 
                RolePermission.select().where(RolePermission.role == role)]
    
    def get_all_roles(self) -> List[Role]:
        """Get list of all available roles."""
        return list(Role.select())
        
    def get_role_by_name(self, name: str) -> Optional[Role]:
        """Find a role by its name."""
        try:
            return Role.get(Role.name == name)
        except DoesNotExist:
            return None