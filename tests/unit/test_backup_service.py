
import os
import shutil
import zipfile
import pytest
from pathlib import Path
from services.backup_service import BackupService

@pytest.fixture
def backup_test_env(tmp_path):
    """Create a temporary environment for backup testing"""
    db_file = tmp_path / "test.db"
    db_file.write_text("dummy database content")
    
    backup_dir = tmp_path / "backups"
    
    return BackupService(backup_dir=str(backup_dir), db_path=str(db_file)), db_file, backup_dir

def test_create_backup(backup_test_env):
    service, db_file, backup_dir = backup_test_env
    
    # Act
    backup_path = service.create_backup("test")
    
    # Assert
    assert os.path.exists(backup_path)
    assert zipfile.is_zipfile(backup_path)
    assert "backup_" in backup_path
    assert "_test" in backup_path

def test_list_backups(backup_test_env):
    service, db_file, backup_dir = backup_test_env
    
    # Create two backups
    service.create_backup("1")
    service.create_backup("2")
    
    # Act
    backups = service.list_backups()
    
    # Assert
    assert len(backups) == 2
    # Should be sorted new to old
    assert "_2" in backups[0]['filename']
    assert "_1" in backups[1]['filename']

def test_delete_backup(backup_test_env):
    service, db_file, backup_dir = backup_test_env
    backup_path = service.create_backup("todelete")
    filename = Path(backup_path).name
    
    # Act
    result = service.delete_backup(filename)
    
    # Assert
    assert result is True
    assert not os.path.exists(backup_path)

def test_restore_backup(backup_test_env):
    service, db_file, backup_dir = backup_test_env
    
    # Modify DB
    db_file.write_text("original content")
    backup_path = service.create_backup("original")
    filename = Path(backup_path).name
    
    # Change DB
    db_file.write_text("changed content")
    
    # Act
    # We need to mock database connection closing if we really tested with a live DB
    # But here we just test file operations
    service.restore_backup(filename)
    
    # Assert
    assert db_file.read_text() == "original content"
    
    # Check that pre-restore backup created
    backups = service.list_backups()
    assert any("pre_restore_auto" in b['filename'] for b in backups)
