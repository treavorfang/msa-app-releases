import os
import sys
from pathlib import Path
import shutil
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

# ============ PATHS CONFIGURATION ============
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    if sys.platform == 'darwin':
        # macOS .app bundle: data is in Contents/Resources
        # sys.executable is in Contents/MacOS/MSA
        BASE_DIR = Path(sys.executable).parent.parent / "Resources"
    else:
        # Windows/Linux: PyInstaller puts data in _internal directory
        BASE_DIR = Path(sys.executable).parent / "_internal"
else:
    # Running from source
    BASE_DIR = Path(__file__).parent.parent

# User Data Directory (Cross-platform: ~/.msa)
USER_DATA_DIR = os.path.join(Path.home(), ".msa")
os.makedirs(USER_DATA_DIR, exist_ok=True)

# Database
DATABASE_NAME = "msa.db"
DATABASE_DIR = "database"

# Use logical database path from flags.py to ensure consistency
try:
    from config.flags import get_db_path
    DATABASE_PATH = get_db_path()
except ImportError:
    # Fallback for circular imports or testing
    DATABASE_PATH = os.path.join(BASE_DIR, DATABASE_DIR, DATABASE_NAME)

BACKUP_DIR = os.path.join(USER_DATA_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# Icons
ICON_DIR = os.path.join(BASE_DIR, "static", "icons")
ICON_PATHS = {
    'eye': os.path.join(ICON_DIR, "eye.png"),
    'edit': os.path.join(ICON_DIR, "edit.png"),
    'trash': os.path.join(ICON_DIR, "trash.png"),
    'plus': os.path.join(ICON_DIR, "plus.png"),
    'device': os.path.join(ICON_DIR, "device.png"),
    'info': os.path.join(ICON_DIR, "info.png"),
    'ticket': os.path.join(ICON_DIR, "ticket.png"),
    # Add all icon paths used in main_window.py
    'dashboard': os.path.join(ICON_DIR, "dashboard.png"),
    'tickets': os.path.join(ICON_DIR, "ticket.png"),
    'devices': os.path.join(ICON_DIR, "device.png"),
    'jobs': os.path.join(ICON_DIR, "jobs.png"),
    'customers': os.path.join(ICON_DIR, "customers.png"),
    'inventory': os.path.join(ICON_DIR, "inventory.png"),
    'reports': os.path.join(ICON_DIR, "reports.png"),
    'settings': os.path.join(ICON_DIR, "settings.png"),
    'technicians': os.path.join(ICON_DIR, "technician.png"),
    'new_ticket': os.path.join(ICON_DIR, "add-ticket.png"),
    'new_customer': os.path.join(ICON_DIR, "user-add.png"),
    'admin': os.path.join(ICON_DIR, "admin.png"),
    'logout': os.path.join(ICON_DIR, "logout.png"),
    'logo': os.path.join(ICON_DIR, "logo.png"),
    'login_banner': os.path.join(ICON_DIR, "login_banner.png"),
    'financial': os.path.join(ICON_DIR, "financial.png"),
}

# Theme
THEME_DIR = os.path.join(BASE_DIR, "static", "theme")

# ============ SECURITY CONFIGURATION ============
PASSWORD_HASH_METHOD = os.getenv('PASSWORD_HASH_METHOD', "pbkdf2:sha256")
PASSWORD_SALT_LENGTH = int(os.getenv('PASSWORD_SALT_LENGTH', 16))
SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 3600))

# ============ APPLICATION CONFIGURATION ============
APP_NAME = "Mobile Service Accounting"
APP_SHORT_NAME = "MSA"

# Import version from auto-generated version.py
try:
    from version import VERSION, FULL_VERSION, BUILD_NUMBER, BUILD_DATE
    APP_VERSION = VERSION
    APP_FULL_VERSION = FULL_VERSION
    APP_BUILD_NUMBER = BUILD_NUMBER
    APP_BUILD_DATE = BUILD_DATE
except ImportError:
    # Fallback if version.py doesn't exist
    APP_VERSION = "1.0.0"
    APP_FULL_VERSION = "1.0.0+build.0"
    APP_BUILD_NUMBER = 0
    APP_BUILD_DATE = "unknown"


# ============ COMPANY CONFIGURATION ============
COMPANY_NAME = "WORLD LOCK Inc"
COMPANY_ADDRESS = "LASHIO, NORTHERN SHAN STATE, MYANMAR"
COMPANY_PHONE = "+959259282400, +959678098642"
COMPANY_MESSAGING_PHONE = "+959259282400" # Whatsapp/Viber/Telegram
COMPANY_WECHAT = "studiotailso"
COMPANY_FACEBOOK = "MSA"
DEVELOPER_NAME = "Sai Hleng"

# ============ THEME CONFIGURATION ============
THEMES = {
    "dark": {
        "name": "Dark Theme",
        "path": os.path.join(THEME_DIR, "theme-dark.css"),
        "description": "Dark theme with gray/blue color scheme"
    },
    "light": {
        "name": "Light Theme",
        "path": os.path.join(THEME_DIR, "theme-light.css"),
        "description": "Light theme with blue accents"
    }
}
DEFAULT_THEME = "dark"

# ============ SETTINGS CONFIGURATION ============
SETTINGS_ORGANIZATION = "MobileServiceAccounting"
SETTINGS_APPLICATION = "MSA"
THEME_SETTING_KEY = "appearance/theme"

# ============ CONFIG FILE PATHS ============
if getattr(sys, 'frozen', False):
    # Frozen: Use configured BASE_DIR and 'config' relative path matched in release.spec
    CONFIG_DIR = os.path.join(BASE_DIR, "config")
else:
    # Dev: Use current directory of config.py
    CONFIG_DIR = os.path.dirname(__file__)

BRANDS_CONFIG_PATH = os.path.join(CONFIG_DIR, "brand_model.ini")
PHONE_ERRORS_CONFIG_PATH = os.path.join(CONFIG_DIR, "phone_error.ini")
# ============ CHANGELOG CONFIGURATION ============
import configparser

def load_changelog():
    """Load changelog from ini file"""
    try:
        ini_path = os.path.join(CONFIG_DIR, "changelog.ini")
        if not os.path.exists(ini_path):
             # Fallback if file missing
             return {
                 "release_highlights": "Highlights not available.",
                 "new_features": [],
                 "improvements": [],
                 "bug_fixes": []
             }
             
        parser = configparser.ConfigParser()
        parser.read(ini_path, encoding='utf-8')
        
        changelog = {}
        
        # Highlights
        if parser.has_section("release_highlights"):
             changelog["release_highlights"] = parser.get("release_highlights", "text", fallback="")
             
        # Lists (features, improvements, fixes)
        for section in ["new_features", "improvements", "bug_fixes"]:
            items = []
            if parser.has_section(section):
                for key, value in parser.items(section):
                    items.append(value.strip('"'))
            changelog[section] = items
            
        return changelog
        
    except Exception as e:
        print(f"Error loading changelog: {e}")
        return {"release_highlights": "Error loading changelog.", "new_features": [], "improvements": [], "bug_fixes": []}

CHANGELOG = load_changelog()

# ============ PLUGINS CONFIGURATION ============
def get_plugin_dir():
    """Get the absolute path to the plugins directory"""
    if getattr(sys, 'frozen', False):
        # PyInstaller Environment
        
        # 1. Check _internal/plugins (bundled inside)
        if hasattr(sys, '_MEIPASS'):
            internal_path = os.path.join(sys._MEIPASS, "plugins")
            if os.path.exists(internal_path):
                return internal_path
                
        # 2. Check plugins/ next to executable (user installed)
        exe_path = os.path.join(os.path.dirname(sys.executable), "plugins")
        if os.path.exists(exe_path):
            return exe_path
            
        return None
    else:
        # Dev Environment
        # Root is 2 levels up from src/app/config
        # We need to go up from config.py -> app -> src -> msa path
        # config.py is in src/app/config
        # __file__ = src/app/config/config.py
        # parent = src/app/config
        # parent.parent = src/app
        # parent.parent.parent = src
        # parent.parent.parent.parent = root (msa)
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "../../../../")) 
        dev_plugin_path = os.path.join(project_root, "plugins")
        
        if os.path.exists(dev_plugin_path):
            return dev_plugin_path
            
        return None

def get_sumatra_path():
    """Get the absolute path to SumatraPDF executable or None if not found"""
    plugin_dir = get_plugin_dir()
    if plugin_dir:
        sumatra_path = os.path.join(plugin_dir, "SumatraPDF.exe")
        if os.path.exists(sumatra_path):
            return sumatra_path
    
    # Check PATH as fallback
    if shutil.which("SumatraPDF.exe"):
        return "SumatraPDF.exe"
        
    return None

import datetime

# ============ UPDATE CONFIGURATION ============
# Split between Private Source and Public Updates
GITHUB_USER = "treavorfang"
GITHUB_REPO_PUBLIC = "msa-app-releases"  # Only for EXE/DMG downloads
UPDATE_CHECK_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO_PUBLIC}/releases/latest"
UPDATE_RELEASE_PAGE = f"https://github.com/treavorfang/{GITHUB_REPO_PUBLIC}/releases"

def log_print_debug(message):
    """Log print-related debug messages to a file for troubleshooting"""
    try:
        log_file = os.path.join(USER_DATA_DIR, "debug_print.log")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Failed to write to debug log: {e}")