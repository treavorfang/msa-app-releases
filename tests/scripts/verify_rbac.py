
from models.user import User
from models.role import Role
from models.permission import Permission
from models.role_permission import RolePermission
from services.role_service import RoleService
from services.audit_service import AuditService
from config.database import initialize_database, db

def verify_rbac():
    print("🚀 Starting RBAC Verification...")
    
    if db.is_closed():
        initialize_database()
        
    audit_service = AuditService()
    role_service = RoleService(audit_service)
    
    # 1. Setup Test Data
    # Ensure default roles exist
    RoleService.create_default_roles(audit_service)
    
    # Create a Test Role
    test_role, _ = Role.get_or_create(name="Test Role")
    test_user = User.create(
        username="rbac_tester", 
        full_name="RBAC Tester",
        role=test_role, 
        email="rbac@test.com", 
        password_hash="hash"
    )
    
    # 2. Test Permission Assignment
    perm_code = "tickets:delete"
    
    # Ensure User doesn't have it yet
    assert not role_service.user_has_permission(test_user, perm_code)
    print(f"✅ User starts without '{perm_code}'")
    
    # Add Permission
    role_service.add_permission_to_role(test_role, perm_code, current_user=None)
    
    # Verify User has it now
    assert role_service.user_has_permission(test_user, perm_code)
    print(f"✅ User HAS '{perm_code}' after assignment")
    
    # 3. Test Permission Removal
    role_service.remove_permission_from_role(test_role, perm_code, current_user=None)
    assert not role_service.user_has_permission(test_user, perm_code)
    print(f"✅ User LOST '{perm_code}' after removal")
    
    # 4. Clean up
    test_user.delete_instance()
    # Clean up role? Maybe keep for manual testing
    # test_role.delete_instance()
    
    print("\n✨ RBAC Verification PASSED!")

if __name__ == "__main__":
    verify_rbac()
