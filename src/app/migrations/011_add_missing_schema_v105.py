from playhouse.migrate import SqliteMigrator, migrate
from peewee import DateTimeField, IntegerField, CharField
from datetime import datetime

def apply(database):
    """Add missing columns and tables for v1.0.5 compatibility."""
    migrator = SqliteMigrator(database)
    
    # 1. Add 'user_id' to technicians if missing
    try:
        columns = [c.name for c in database.get_columns('technicians')]
        if 'user_id' not in columns:
            user_id_field = IntegerField(null=True)
            migrate(
                migrator.add_column('technicians', 'user_id', user_id_field)
            )
            print("Added 'user_id' column to technicians table.")
    except Exception as e:
        print(f"Error adding 'user_id' to technicians: {e}")
    
    # 2. Create ticket_photos table if it doesn't exist
    try:
        tables = [t for t in database.get_tables()]
        if 'ticket_photos' not in tables:
            database.execute_sql('''
                CREATE TABLE IF NOT EXISTS ticket_photos (
                    id INTEGER NOT NULL PRIMARY KEY,
                    ticket_id INTEGER NOT NULL,
                    image_path VARCHAR(500) NOT NULL,
                    photo_type VARCHAR(50) DEFAULT 'general',
                    description VARCHAR(255),
                    created_at DATETIME NOT NULL,
                    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
                )
            ''')
            print("Created 'ticket_photos' table.")
    except Exception as e:
        print(f"Error creating ticket_photos table: {e}")

def revert(database):
    """Optional revert logic."""
    pass
