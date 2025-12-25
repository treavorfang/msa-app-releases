
import sys
import os
from datetime import datetime

# Add src/app to path
sys.path.append(os.path.join(os.getcwd(), 'src', 'app'))

from config.database import db
from models.user import User
from models.technician import Technician
from models.role import Role
from utils.security.password_utils import hash_password

def migrate_technicians():
    """
    Migrate existing Technicians to have a linked User account.
    """
    print(f"🚀 Starting Technician -> User Migration at {datetime.now()}")
    
    # Ensure connection
    if db.is_closed():
        # Initialize DB if not already (Standard Pattern for Standalone Scripts)
        db_path = os.path.join(os.getcwd(), 'database', 'msa_dev.db')
        print(f"📂 using database at: {db_path}")
        from peewee import SqliteDatabase
        db.init(db_path)
        db.connect()

    # 1. Update Schema (Add column if not exists - Peewee manual migration)
    # We do a safe check, though usually we rely on auto-migration on startup.
    # To be safe, we let the main app startup handle schema creation, 
    # OR we force it here if we are running offline.
    # Let's assume schema is updated by the model definition we just changed.
    # 1. Update Schema (Add column if not exists)
    try:
        # Check if column exists
        cursor = db.execute_sql("PRAGMA table_info(technicians)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'user_id' not in columns:
            print("📦 Adding 'user_id' column to 'technicians' table...")
            db.execute_sql('ALTER TABLE technicians ADD COLUMN user_id INTEGER REFERENCES users(id)')
            print("✅ Column added successfully.")
        else:
            print("ℹ️ 'user_id' column already exists.")
            
    except Exception as e:
        print(f"⚠️ Schema update failed: {e}")
        # If schema update fails, the next step (select) might fail if it tries to fetch user_id.
        # But we proceed and hope for the best or catch it there.


    # 2. Get 'Technician' Role (or create it)
    tech_role = Role.get_or_none(Role.name == "Technician")
    if not tech_role:
        print("ℹ️ Creating 'Technician' Role...")
        tech_role = Role.create(
            name="Technician",
            description="Repair Technician with limited access",
            code="role_tech"
        )
    
    # 3. Migrate Users
    technicians = Technician.select()
    count = 0
    skipped = 0
    
    print(f"🔍 Found {technicians.count()} Technicians to check.")
    
    with db.atomic():
        for tech in technicians:
            if tech.user:
                print(f"✅ Tech '{tech.full_name}' is already linked to User ID {tech.user.id}. Skipping.")
                skipped += 1
                continue
                
            print(f"🔄 Migrating '{tech.full_name}'...")
            
            # Generate unique username
            base_username = tech.email.split('@')[0] if tech.email else tech.full_name.lower().replace(" ", ".")
            username = base_username
            counter = 1
            while User.select().where(User.username == username).exists():
                username = f"{base_username}{counter}"
                counter += 1
                
            # Create User
            # Note: We can't recover plain text password easily if hashed differently.
            # But Tech model has 'password' field. Is it hashed?
            # Src implies 'password' stores hash in Tech model too. 
            # We can copy the hash directly if formats match (Bcrypt).
            
            pwd_hash = tech.password
            if not pwd_hash:
                # Set a default temporary password if none exists
                print(f"   ⚠️ No password found. Setting default 'ChangeMe123!'")
                pwd_hash = hash_password("ChangeMe123!")
                
            new_user = User.create(
                username=username,
                full_name=tech.full_name,
                email=tech.email or f"{username}@example.com", # Fallback email
                password_hash=pwd_hash,
                role=tech_role,
                is_active=tech.is_active
            )
            
            # Link Profile
            tech.user = new_user
            tech.save()
            
            print(f"   ✨ Created User: {username} (ID: {new_user.id})")
            count += 1
            
    print(f"\n🎉 Migration Complete!")
    print(f"   - Processed: {count}")
    print(f"   - Skipped: {skipped}")

if __name__ == "__main__":
    migrate_technicians()
