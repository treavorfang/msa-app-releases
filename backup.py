import os
import shutil
import datetime
from pathlib import Path

def create_backup():
    # Project root directory
    project_root = Path(__file__).parent.parent
    
    # Backup directory
    backup_dir = project_root / "backup"
    backup_dir.mkdir(exist_ok=True)
    
    # Create timestamped backup folder
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}"
    backup_path = backup_dir / backup_name
    
    # Files/directories to include
    include = [
        "src",
        # "tests",
        # "README.md",
        # "requirements.txt"
    ]
    
    # Create backup
    print(f"Creating backup at {backup_path}")
    backup_path.mkdir(parents=True, exist_ok=True)
    
    for item in include:
        src_item = project_root / item
        dst_item = backup_path / item
        
        if src_item.exists():
            if src_item.is_dir():
                shutil.copytree(src_item, dst_item, 
                               ignore=shutil.ignore_patterns(
                                   '__pycache__', 
                                   '*.pyc', 
                                   '.DS_Store'
                               ))
            else:
                shutil.copy2(src_item, dst_item)
    
    # Create zip archive
    shutil.make_archive(str(backup_path), 'zip', backup_path)
    print(f"Backup complete: {backup_path}.zip")

if __name__ == "__main__":
    create_backup()