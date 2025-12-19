
import sys
import os
from pathlib import Path

# Add src/app to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src', 'app'))

from absl import flags
from config.flags import get_db_path, FLAGS

def test_db_paths():
    print("Testing DB Paths...")

    # Mock flags
    flags.FLAGS(['test_script'])
    
    # Test Development
    FLAGS.env = 'development'
    dev_path = get_db_path()
    print(f"Development Path: {dev_path}")
    assert "database/msa_dev.db" in dev_path
    if "src/app" in dev_path:
        print("⚠️  Warning: Development DB is still in src/app!")
    else:
        print("✅ Development DB is outside src/app")

    # Test Production
    FLAGS.env = 'production'
    prod_path = get_db_path()
    print(f"Production Path: {prod_path}")
    
    if sys.platform == "darwin":
        assert "Application Support/MSA/msa.db" in prod_path
    elif sys.platform == "win32":
        assert "AppData" in prod_path and "MSA" in prod_path
    
    # Test Staging
    FLAGS.env = 'staging'
    staging_path = get_db_path()
    print(f"Staging Path: {staging_path}")
    assert "msa_staging.db" in staging_path

    print("✅ All path tests passed!")

if __name__ == "__main__":
    test_db_paths()
