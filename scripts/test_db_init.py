
import sys
import os
from pathlib import Path

# Add src/app to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src', 'app'))

from config.database import initialize_database, db
from config.flags import FLAGS

def test_init():
    print("Testing DB Initialization...")
    
    # Force dev
    FLAGS(['test'])
    FLAGS.env = 'development'
    
    initialize_database()
    
    print(f"DB Initialized: {db.database}")
    
    # Check if a file was created or expected
    expected_path = os.path.join(os.getcwd(), 'database', 'msa_dev.db')
    if str(db.database) == expected_path:
        print("✅ DB path matches expected development path.")
    else:
        print(f"❌ DB path mismatch! Got {db.database}, expected {expected_path}")

if __name__ == "__main__":
    test_init()
