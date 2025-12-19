#!/usr/bin/env python3
"""
Script to fix corrupted invoice_device_id index
"""
from config.database import db

def fix_index():
    print("Connecting to database...")
    db.connect()
    
    try:
        # Drop the corrupted index
        print("Dropping corrupted index 'invoice_device_id'...")
        db.execute_sql('DROP INDEX IF EXISTS invoice_device_id;')
        
        # Recreate the index
        print("Recreating index 'invoice_device_id'...")
        db.execute_sql('CREATE INDEX invoice_device_id ON invoices (device_id);')
        
        # Verify integrity
        print("\nVerifying database integrity...")
        result = db.execute_sql('PRAGMA integrity_check;').fetchone()
        
        if result[0] == 'ok':
            print("✓ Database integrity check passed!")
        else:
            print(f"⚠ Integrity check result: {result[0]}")
        
        print("\n✓ Index successfully rebuilt!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        db.close()
        print("Database connection closed.")

if __name__ == "__main__":
    fix_index()
