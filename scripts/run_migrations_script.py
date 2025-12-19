
import sys
import os

# Add src/app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'app')))

from services.migration_service import MigrationService

if __name__ == "__main__":
    print("🚀 Running Migrations...")
    service = MigrationService()
    try:
        service.run_migrations()
        print("✅ Migrations Complete.")
    except Exception as e:
        print(f"❌ Migration Failed: {e}")
        sys.exit(1)
