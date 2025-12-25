import hashlib
import binascii
import os
from playhouse.migrate import SqliteMigrator, migrate
from peewee import CharField

# Minimal dummy config for salt length if we can't import properly
# But we'll try to use the real one first.
try:
    from config.config_manager import PASSWORD_SALT_LENGTH
except ImportError:
    PASSWORD_SALT_LENGTH = 16

def hash_password_simple(password: str) -> str:
    """Re-implementation of hash_password to avoid complex dependency issues in migration."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')[:PASSWORD_SALT_LENGTH]
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

def apply(database):
    migrator = SqliteMigrator(database)
    
    # 1. Migrate data ONLY if the column exists
    try:
        columns = [c.name for c in database.get_columns('technicians')]
        if 'pin' in columns:
            print("Found legacy 'pin' column. Migrating data...")
            cursor = database.execute_sql('SELECT id, pin, password FROM technicians WHERE pin IS NOT NULL')
            rows = cursor.fetchall()
            
            for tech_id, pin, password in rows:
                if pin and not password:
                    hashed = hash_password_simple(pin)
                    database.execute_sql('UPDATE technicians SET password = ? WHERE id = ?', (hashed, tech_id))
                    print(f"Migrated and hashed PIN for technician ID {tech_id}")

            # 2. Drop the 'pin' column
            migrate(
                migrator.drop_column('technicians', 'pin')
            )
            print("Successfully dropped 'pin' column.")
        else:
            print("Migration 010: No 'pin' column found, skipping legacy migration.")
    except Exception as e:
        print(f"Error during legacy 'pin' migration: {e}")

def revert(database):
    """Revert is difficult as we can't unhash, but we can re-add the column."""
    migrator = SqliteMigrator(database)
    pin_field = CharField(max_length=4, null=True, help_text="4-digit mobile login PIN")
    migrate(
        migrator.add_column('technicians', 'pin', pin_field)
    )
