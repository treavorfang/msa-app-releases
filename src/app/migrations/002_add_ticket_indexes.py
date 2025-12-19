
from config.database import db

def apply(database):
    """Add indexes to Ticket table"""
    print("Applying migration: 002_add_ticket_indexes")
    
    # Check if we are using SQLite, if so index creation syntax is standard
    # Peewee database wrapper provides 'execute_sql'
    
    # List of indexes to create
    indexes = [
        ("idx_tickets_status", "tickets", ["status"]),
        ("idx_tickets_created_at", "tickets", ["created_at"]),
        ("idx_tickets_branch_id", "tickets", ["branch_id"]),
        ("idx_tickets_is_deleted", "tickets", ["is_deleted"]),
        ("idx_tickets_technician", "tickets", ["assigned_technician_id"])
    ]
    
    for idx_name, table, columns in indexes:
        try:
            # Check if index exists first to be safe (SQLite)
            # select name from sqlite_master where type='index' and name='idx_tickets_status'
            check_sql = "SELECT name FROM sqlite_master WHERE type='index' AND name=?"
            cursor = database.execute_sql(check_sql, (idx_name,))
            if cursor.fetchone():
                print(f"Index {idx_name} already exists. Skipping.")
                continue
                
            col_str = ", ".join(columns)
            sql = f"CREATE INDEX {idx_name} ON {table} ({col_str})"
            database.execute_sql(sql)
            print(f"Created index {idx_name}")
        except Exception as e:
            print(f"Failed to create index {idx_name}: {e}")

def revert(database):
    """Drop indexes"""
    indexes = [
        "idx_tickets_status",
        "idx_tickets_created_at",
        "idx_tickets_branch_id",
        "idx_tickets_is_deleted",
        "idx_tickets_technician"
    ]
    
    for idx_name in indexes:
        try:
            sql = f"DROP INDEX IF EXISTS {idx_name}"
            database.execute_sql(sql)
            print(f"Dropped index {idx_name}")
        except Exception as e:
            print(f"Failed to drop index {idx_name}: {e}")
