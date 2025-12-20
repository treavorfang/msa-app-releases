import os
import shutil
import datetime
from pathlib import Path

def create_backup():
    # Project root directory - assuming backup.py is in the project root
    project_root = Path(__file__).parent.resolve()
    
    # Backup directory
    backup_dir = project_root / "backup"
    backup_dir.mkdir(exist_ok=True)
    
    # Create timestamped backup folder
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"msa_backup_{timestamp}"
    backup_path = backup_dir / backup_name
    
    # Files/directories to include
    include = [
        "src",
        "tools",
        "scripts",
        "docs",
        "tests",
        "plugins",
        "test_data",
        "main.py",
        "msa_backend_code.py",
        "monitor_startup.py",
        "requirements.txt",
        "requirements-test.txt",
        "version.json",
        "build.bat",
        "build_windows.bat",
        "build_macos.sh",
        "build_cython.py",
        "release_mac.spec",
        "release_win.spec",
        "GITHUB_GUIDE.md",
        "WINDOWS_BUILD_GUIDE.md",
        "firebase_functions_guide.md",
        "activation_refinement_plan.md"
    ]
    
    # Create backup directory
    print(f"Creating backup at {backup_path}")
    backup_path.mkdir(parents=True, exist_ok=True)
    
    for item in include:
        src_item = project_root / item
        dst_item = backup_path / item
        
        if src_item.exists():
            if src_item.is_dir():
                # print(f"Copying directory: {item}")
                shutil.copytree(src_item, dst_item, 
                               ignore=shutil.ignore_patterns(
                                   '__pycache__', 
                                   '*.pyc', 
                                   '.DS_Store',
                                   '.git',
                                   '.vscode',
                                   'dist',
                                   'build',
                                   'venv',
                                   '.env'
                               ))
            else:
                # print(f"Copying file: {item}")
                shutil.copy2(src_item, dst_item)
        else:
            print(f"Warning: {item} not found")
    
    # Create zip archive
    shutil.make_archive(str(backup_path), 'zip', backup_path)
    print(f"Backup complete: {backup_path}.zip")
    
    # Optional: Remove the unzipped folder after zipping to save space
    # shutil.rmtree(backup_path)

if __name__ == "__main__":
    create_backup()