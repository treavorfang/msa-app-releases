"""BackupService - Database Backup and Restore.

This service handles creating ZIP archives of the SQLite database
and restoring from them, including safety checks and automatic pre-restore backups.
"""

import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Union
from config.config import BACKUP_DIR, DATABASE_PATH


class BackupService:
    """Service class for Database Backup operations."""
    
    def __init__(self, backup_dir: Optional[Union[str, Path]] = None, db_path: Optional[Union[str, Path]] = None):
        """Initialize BackupService.
        
        Args:
            backup_dir: Directory to store backups (defaults to config)
            db_path: Path to database file (defaults to config)
        """
        self.backup_dir = Path(backup_dir) if backup_dir else Path(BACKUP_DIR)
        self.db_path = Path(db_path) if db_path else Path(DATABASE_PATH)
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """Ensure backup directory exists."""
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)

    def create_backup(self, note: Optional[str] = None) -> str:
        """Create a backup of the database.
        
        Args:
            note: Optional suffix for the backup filename
            
        Returns:
            str: Path to the created backup file
            
        Raises:
            FileNotFoundError: If DB file doesn't exist
            Exception: If backup creation fails
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}"
        if note:
            # Sanitize note
            safe_note = "".join(c for c in note if c.isalnum() or c in ('-', '_'))
            filename += f"_{safe_note}"
        
        filename += ".zip"
        backup_path = self.backup_dir / filename

        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(self.db_path, self.db_path.name)
            return str(backup_path)
        except Exception as e:
            raise Exception(f"Failed to create backup: {e}")

    def list_backups(self) -> List[Dict]:
        """List all available backups sorted by date (newest first).
        
        Returns:
            List[Dict]: List of backup details (filename, path, size, created_at)
        """
        backups = []
        if not self.backup_dir.exists():
            return []

        for item in self.backup_dir.glob("backup_*.zip"):
            stats = item.stat()
            backups.append({
                'filename': item.name,
                'path': str(item),
                'size': stats.st_size,
                'created_at': datetime.fromtimestamp(stats.st_ctime)
            })
        
        return sorted(backups, key=lambda x: x['created_at'], reverse=True)

    def restore_backup(self, backup_filename: str) -> bool:
        """Restore database from a backup file.
        
        Automatically creates a 'pre_restore_auto' backup before proceeding.
        Closes the database connection if open.
        """
        backup_path = self.backup_dir / backup_filename
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Create a temp backup of current state just in case
        try:
            self.create_backup("pre_restore_auto")
        except:
            pass # Ignore if it fails, we want to try restore

        try:
            # Close DB connection if open
            from config.database import db
            if not db.is_closed():
                db.close()

            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Extract to parent directory, overwriting existing DB
                zipf.extract(self.db_path.name, self.db_path.parent)
                
            return True
        except Exception as e:
            raise Exception(f"Failed to restore backup: {e}")

    def delete_backup(self, backup_filename: str) -> bool:
        """Delete a backup file."""
        backup_path = self.backup_dir / backup_filename
        if backup_path.exists():
            os.remove(backup_path)
            return True
        return False
