"""
Main application entry point for MSA (Mobile Service Accounting).

This module initializes the application, sets up the database,
runs migrations, and starts the Qt application.

Usage:
    python main.py [--env=development|production] [--debug=true|false]
    python main.py --flagfile=config/production.flags
"""

import sys
import atexit
from absl import app, flags
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings

# Local imports
from config.database import initialize_database
from config.config_manager import SETTINGS_ORGANIZATION, SETTINGS_APPLICATION
from config.flags import FLAGS, get_config, is_development
# from core.app import MSA # Deferred import
# from services.backup_service import BackupService # Deferred import
# from services.migration_service import MigrationService # Deferred import

# Import flags module to register all flags
import config.flags


def cleanup():
    """
    Cleanup handler executed on application exit.
    
    Creates an automatic backup of the database before the application closes.
    Errors during backup are caught and logged to prevent exit failures.
    """
    try:
        from services.backup_service import BackupService
        print("Creating auto-backup on exit...")
        BackupService().create_backup("auto_exit")
    except Exception as e:
        print(f"Backup failed: {e}")


def update_version_info():
    """
    Update version information in development mode.
    
    Runs the generate_version.py script to update build numbers and version info.
    Only executed in development mode to avoid overhead in production.
    """
    try:
        import subprocess
        import os
        
        # Calculate project root (main.py is in src/app, so go up 2 levels)
        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        )
        script_path = os.path.join(project_root, 'scripts', 'generate_version.py')
        
        if not os.path.exists(script_path):
            return
            
        print("🔧 Updating version information...")
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Version updated (Changes will apply on next restart)")
            # Parse and display version info
            for line in result.stdout.splitlines():
                if "Full version:" in line or "Version:" in line:
                    print(f"   {line.strip()}")
        else:
            print(f"⚠️  Version update failed: {result.stderr}")
            
    except Exception as e:
        print(f"⚠️  Failed to check/update version: {e}")


def initialize_settings():
    """
    Initialize Qt settings with default values.
    
    Sets up QSettings with organization and application name,
    and applies default theme if not already configured.
    
    Returns:
        QSettings: Configured settings object
    """
    settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
    
    # Apply theme from flags if not already set
    if not settings.value("appearance/theme"):
        settings.setValue("appearance/theme", FLAGS.theme)
    
    return settings


def run_database_migrations():
    """
    Initialize database and run pending migrations.
    
    Raises:
        Exception: If migrations fail critically (currently catches and continues)
    """
    # Initialize database connection and models
    initialize_database()
    
    # Run migrations
    try:
        from services.migration_service import MigrationService
        print("Running database migrations...")
        MigrationService().run_migrations()
    except Exception as e:
        print(f"CRITICAL: Failed to run migrations: {e}")
        # TODO: In production, should exit on migration failure
        # sys.exit(1)


def start_mobile_server():
    """
    Start the background API server for mobile access.
    
    Returns:
        ServerWorker: The worker thread if started, None otherwise
    """
    try:
        from api.worker import ServerWorker
        from config.flags import FLAGS
        
        if not FLAGS.enable_mobile_server:
            print("📱 Mobile server is disabled by config.")
            return None
            
        print(f"📱 Starting Mobile API Server on port {FLAGS.mobile_server_port}...")
        worker = ServerWorker(port=FLAGS.mobile_server_port)
        worker.start()
        return worker
    except Exception as e:
        print(f"⚠️  Failed to start Mobile API Server: {e}")
        return None


def main(argv):
    """
    Main application entry point.
    
    Initializes the application in the following order:
    1. Load configuration
    2. Update version (development only)
    3. Initialize settings
    4. Setup database and run migrations
    5. Configure Qt styling
    6. Start the application
    
    Args:
        argv: Command line arguments (handled by absl.app)
        
    Returns:
    """
    # Check for single instance using QLockFile (more robust against crashes)
    from PySide6.QtCore import QLockFile, QDir
    from PySide6.QtWidgets import QMessageBox

    # Lock file path in temp directory
    lock_file_path = QDir.tempPath() + "/msa_instance.lock"
    lock_file = QLockFile(lock_file_path)
    
    # Try to lock
    # setStaleLockTime(0) means we don't trust old locks automatically, but tryLock handles ownership.
    # Actually, default behavior of tryLock checks PID.
    
    if not lock_file.tryLock(100): # Wait 100ms max
        # Failed to lock, meaning another instance has it
        temp_app = QApplication(sys.argv)
        QMessageBox.warning(None, "Already Running", 
                           "An instance of MSA is already running.")
        return 0

    # Get configuration from flags
    # Detect if running as frozen application (PyInstaller)
    if getattr(sys, 'frozen', False):
        # Force production mode if not explicitly overridden by command line
        # (Assuming normal launch is no args, sticking with 'development' default would be bad)
        print("❄️  Running in frozen mode: Forcing Production environment")
        FLAGS.env = 'production'

    # Load language preference from QSettings (persisted from previous sessions)
    # This ensures logs and initial config reflect the user's choice
    settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
    saved_language = settings.value("system/language")
    if saved_language:
        FLAGS.language = saved_language

    config = get_config()
    
    # Print startup information in development mode
    if is_development():
        print(f"🚀 Starting MSA in {FLAGS.env} mode")
        print(f"📊 Configuration: {config}")
        update_version_info()
    
    # Initialize Qt settings
    initialize_settings()
    
    # Setup database and migrations
    run_database_migrations()
    
    # Set Qt style for consistent theming (Matches backup v1.0.4)
    QApplication.setStyle('Fusion')

    # Start mobile API server
    mobile_server = start_mobile_server()
    
    # Initialize and run the application
    # Note: MSA creates its own QApplication instance
    from core.app import MSA
    auth_app = MSA()
    
    # Store reference to keep it alive
    if mobile_server:
        auth_app.mobile_server = mobile_server
    
    try:
        result = auth_app.app.exec()
    finally:
        # Stop mobile server on exit
        if mobile_server:
            mobile_server.stop()
            
    return result


# Register cleanup handler
atexit.register(cleanup)


# --- CRASH LOGGING FOR WINDOWS DEBUGGING ---
# This block ensures that if the app crashes silently (common in frozen GUI apps),
# we get a log file with the error.
if __name__ == "__main__":
    try:
        # Redirect stdout/stderr to file only if frozen (exe)
        if getattr(sys, 'frozen', False):
            import os
            from datetime import datetime
            from pathlib import Path
            
            # Determine robust user data directory (matches flags.py logic)
            app_name = "MSA"
            if sys.platform == "win32":
                base_dir = Path(os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming")))
            elif sys.platform == "darwin":
                base_dir = Path(os.path.expanduser("~/Library/Application Support"))
            else:
                base_dir = Path(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")))
            
            # Create logs directory in AppData/MSA/logs
            log_dir = base_dir / app_name / "logs"
            
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                # Fallback to home/MSA_Logs if permission denied
                log_dir = Path(os.path.expanduser("~")) / "MSA_Logs"
                log_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamped filename: crash_YYYYMMDD_HHMMSS.log
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = log_dir / f"crash_{timestamp}.log"
                
            sys.stdout = open(log_path, "a", buffering=1, encoding='utf-8')
            sys.stderr = open(log_path, "a", buffering=1, encoding='utf-8')
            
            print(f"Platform: {sys.platform}")


        sys.exit(app.run(main))
        
    except Exception as e:
        # Catch CRITICAL startup errors
        import traceback
        error_msg = f"CRITICAL STARTUP ERROR:\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        
        # Also try to show a native popup if possible
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, error_msg, "MSA Startup Error", 0x10)
        except:
            pass
            
        sys.exit(1)