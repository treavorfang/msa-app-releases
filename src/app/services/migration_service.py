"""MigrationService - Database Schema Migration Manager.

This service discovers and applies database migrations from the 'migrations' directory.
It tracks applied versions in the 'schema_versions' table and handles legacy database detection.
"""

import importlib
import os
import re
from datetime import datetime
from typing import List, Tuple
from peewee import OperationalError
from config.database import db
from models.schema_version import SchemaVersion
from models.user import User


class MigrationService:
    """Service class for Database Migration operations."""
    
    def __init__(self):
        """Initialize MigrationService."""
        import sys
        if getattr(sys, 'frozen', False):
            # In PyInstaller, the base path is sys._MEIPASS
            # We bundle migrations into a 'migrations' folder in the root of the bundle
            base_path = sys._MEIPASS
            self.migrations_dir = os.path.join(base_path, 'migrations')
        else:
            # Development mode
            self.migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')
    
    def initialize(self):
        """Ensure migration tracking table exists and handle legacy databases.
        
        If User table exists but SchemaVersion does not, it assumes an existing
        database and marks the initial schema as applied.
        """
        db.connect(reuse_if_open=True)
        db.create_tables([SchemaVersion], safe=True)
        
        # Check if we are on a legacy DB (User exists but no migration entries)
        if User.table_exists() and SchemaVersion.select().count() == 0:
            print("Detected existing database. Marking initial schema as applied.")
            self._mark_as_applied(1, "initial_schema")

    def run_migrations(self):
        """Discover and apply all pending migrations."""
        self.initialize()
        
        # Get applied versions
        applied_versions = {v.version for v in SchemaVersion.select()}
        
        # Discover migration files
        migration_files = self._get_migration_files()
        
        for version, name, filename in migration_files:
            if version not in applied_versions:
                print(f"Applying migration {version}: {name}...")
                try:
                    self._apply_migration(filename)
                    self._mark_as_applied(version, name)
                    print(f"Successfully applied {version}: {name}")
                except Exception as e:
                    print(f"Failed to apply migration {version}: {e}")
                    raise e
            else:
                # Migration already applied
                pass

    def _get_migration_files(self) -> List[Tuple[int, str, str]]:
        """Return list of (version, name, filename) sorted by version.
        
        Scans the migrations directory for files matching 'N_name.py'.
        """
        files = []
        pattern = re.compile(r'^(\d+)_+(.+)\.py$')
        
        if not os.path.exists(self.migrations_dir):
            os.makedirs(self.migrations_dir)
            
        for filename in os.listdir(self.migrations_dir):
            match = pattern.match(filename)
            if match:
                version = int(match.group(1))
                name = match.group(2)
                files.append((version, name, filename))
        
        return sorted(files, key=lambda x: x[0])

    def _apply_migration(self, filename: str):
        """Import module and run its apply() function."""
        import sys
        if getattr(sys, 'frozen', False):
            # Ensure the directory containing the 'migrations' folder is in sys.path
            import sys
            base_dir = sys._MEIPASS
            if base_dir not in sys.path:
                sys.path.insert(0, base_dir)

        module_name = f"migrations.{filename[:-3]}"
        module = importlib.import_module(module_name)
        
        if hasattr(module, 'apply'):
            with db.atomic():
                module.apply(db)
        else:
            print(f"Warning: No apply() function in {filename}")

    def _mark_as_applied(self, version: int, name: str):
        """Record a successful migration in the database."""
        SchemaVersion.create(
            version=version,
            name=name,
            applied_at=datetime.now()
        )
