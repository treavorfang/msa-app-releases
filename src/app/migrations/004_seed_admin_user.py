from datetime import datetime
from config.database import db
from models.user import User
from models.role import Role
from utils.security.password_utils import hash_password

def apply(database):
    """Seed the default admin user if no users exist."""
    
    if User.select().count() == 0:
        # Ensure Admin Role exists
        admin_role = Role.get_or_none(Role.name == 'admin')
        if not admin_role:
            admin_role = Role.create(name='admin', description='Administrator')
            
        print("Creating default admin user...")
        User.create(
            username='admin',
            email='admin@msa.com',
            full_name='System Administrator',
            password_hash=hash_password('admin123'),
            is_active=True,
            role=admin_role,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        print("✅ Default Admin User Created: admin / admin123")
    else:
        print("Users already exist. Skipping default admin creation.")

def revert(database):
    pass
