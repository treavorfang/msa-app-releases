
from peewee import OperationalError

def apply(database):
    """Add new customization fields to business_settings table."""
    print("Applying migration: 005_add_customization_to_settings")
    
    fields = [
        ("ticket_number_format", "VARCHAR(255) DEFAULT 'RPT-{branch}{date}-{seq}'"),
        ("invoice_number_format", "VARCHAR(255) DEFAULT 'INV-{branch}{date}-{seq}'"),
        ("po_number_format", "VARCHAR(255) DEFAULT 'PO-{branch}{date}-{seq}'"),
        ("ticket_terms", "TEXT"),
        ("invoice_terms", "TEXT")
    ]
    
    for field_name, field_type in fields:
        try:
            # Check if column exists
            check_sql = f"PRAGMA table_info(business_settings)"
            cursor = database.execute_sql(check_sql)
            columns = [row[1] for row in cursor.fetchall()]
            
            if field_name in columns:
                print(f"Column {field_name} already exists in business_settings. Skipping.")
                continue
                
            sql = f"ALTER TABLE business_settings ADD COLUMN {field_name} {field_type}"
            database.execute_sql(sql)
            print(f"Added column {field_name} to business_settings")
        except Exception as e:
            print(f"Failed to add column {field_name}: {e}")

def revert(database):
    """SQLite does not support dropping columns easily. This would require table recreation."""
    pass
