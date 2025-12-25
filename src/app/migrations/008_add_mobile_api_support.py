from playhouse.migrate import SqliteMigrator, migrate
from peewee import CharField
from models.technician import Technician
from models.ticket_photo import TicketPhoto

def apply(database):
    migrator = SqliteMigrator(database)
    
    # PIN column addition removed as it was immediately superseded by 
    # hashed passwords in migration 010.

    # 2. Create ticket_photos table
    database.create_tables([TicketPhoto], safe=True)
    print("Created 'ticket_photos' table.")

def revert(database):
    """Revert changes (optional/dangerous)"""
    # migrator = SqliteMigrator(database)
    # migrate(migrator.drop_column('technicians', 'pin'))
    # database.drop_tables([TicketPhoto])
    pass
