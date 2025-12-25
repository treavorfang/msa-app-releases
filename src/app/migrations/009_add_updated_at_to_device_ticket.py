from playhouse.migrate import SqliteMigrator, migrate
from peewee import DateTimeField
from datetime import datetime

def apply(database):
    migrator = SqliteMigrator(database)
    
    updated_at_field = DateTimeField(default=datetime.now, help_text="Last update timestamp")
    
    # 1. Add 'updated_at' to devices
    try:
        columns = [c.name for c in database.get_columns('devices')]
        if 'updated_at' not in columns:
            migrate(
                migrator.add_column('devices', 'updated_at', updated_at_field)
            )
            print("Added 'updated_at' column to devices table.")
    except Exception as e:
        print(f"Error adding 'updated_at' to devices: {e}")

    # 2. Add 'updated_at' to tickets
    try:
        columns = [c.name for c in database.get_columns('tickets')]
        if 'updated_at' not in columns:
            migrate(
                migrator.add_column('tickets', 'updated_at', updated_at_field)
            )
            print("Added 'updated_at' column to tickets table.")
    except Exception as e:
        print(f"Error adding 'updated_at' to tickets: {e}")

def revert(database):
    """Optional revert logic"""
    pass
