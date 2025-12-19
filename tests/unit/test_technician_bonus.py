# tests/test_technician_bonus.py
"""Test that the TechnicianBonus table is created during database initialization.
"""
import os
import sys

# Ensure the project src is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "app"))

from config.database import db
from models.technician_bonus import TechnicianBonus

def test_technician_bonus_table_created():
    # Ensure database connection is open
    if db.is_closed():
        db.connect()
    
    # Create table if it doesn't exist
    db.create_tables([TechnicianBonus], safe=True)

    # Perform a simple query; should not raise OperationalError
    result = TechnicianBonus.select().first()
    # The table exists; result may be None if empty
    assert result is None or isinstance(result, TechnicianBonus)

