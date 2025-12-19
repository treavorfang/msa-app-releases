"""
Main application class for MSA (Mobile Service Accounting).

This module contains the MSA class which manages the application lifecycle,
including authentication, window management, and theme initialization.
"""

import sys
import platform
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from PySide6.QtGui import QFont

# Local imports
# from controllers.auth_controller import AuthController # Deferred import
# from core.dependency_container import DependencyContainer # Deferred import
from utils.language_manager import language_manager


class MSA:
    """
    Main application class managing the MSA application lifecycle.
    
    Responsibilities:
    - QApplication initialization
    - Cross-platform font configuration
    - Dependency injection container setup
    - Theme management
    - Authentication flow
    - Window management (login -> main window)
    
    Attributes:
        app (QApplication): The Qt application instance
        container (DependencyContainer): Dependency injection container
        auth_controller (AuthController): Authentication controller
        current_window (QWidget): Currently displayed window
        main_window (MainWindow): Main application window (after login)
    """
    
    # Platform-specific font configuration
    PLATFORM_FONTS = {
        "Darwin": (".AppleSystemUIFont", 13),  # macOS
        "Windows": ("Segoe UI", 10),           # Windows
        "Linux": ("Ubuntu", 11),               # Linux
    }
    
    def __init__(self):
        """
        Initialize the MSA application.
        
        Initialization order (Optimized):
        1. Set Windows AppUserModelID
        2. Create QApplication
        3. Show Login Window (Visual feedback immediately)
        4. Configure fonts/theme
        5. Defer heavy dependency loading
        """
        # Windows taskbar icon fix
        if sys.platform == 'win32':
            import ctypes
            myappid = 'msa.app.1.0.0'  # Arbitrary ID
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception as e:
                print(f"Failed to set AppUserModelID: {e}")

        # Create or get existing QApplication instance
        self.app = QApplication.instance() or QApplication(sys.argv)
        # Prevent app from quitting when switching windows
        self.app.setQuitOnLastWindowClosed(False)
        
        # Set application icon
        from PySide6.QtGui import QIcon
        from config.config import ICON_PATHS
        if 'logo' in ICON_PATHS:
            self.app.setWindowIcon(QIcon(ICON_PATHS['logo']))
        
        # Configure platform-specific fonts - DEPRECATED/REMOVED to use system defaults
        # self._configure_fonts()
        
        # --- FIX: Load Theme EARLY to prevent FOUC (Flash of Unstyled Content) ---
        try:
             from controllers.theme_controller import ThemeController
             # Initialize a temporary controller to load the theme immediately
             # This ensures the window opens with the correct dark/light theme, avoiding the glitch
             theme_ctl = ThemeController(self.app)
             theme_ctl.load_theme(theme_ctl.current_theme)
             print(f"✓ Theme pre-loaded: {theme_ctl.current_theme}")
        except Exception as e:
             print(f"Failed to pre-load theme: {e}")
        # -------------------------------------------------------------------------
        
        # Run language settings migration (one-time, safe to run multiple times)
        # self._migrate_language_settings()
        
        # Load system language using QSettings (persists across restarts for Login Screen)
        # Must do this BEFORE auth/login init so Login screen has correct language
        from PySide6.QtCore import QSettings
        from config.config_manager import SETTINGS_ORGANIZATION, SETTINGS_APPLICATION
        settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
        last_lang = settings.value("system/language", "en")
        language_manager.load_language(last_lang)

        # Initialize window management
        self.current_window = None

        # Start initialization
        from PySide6.QtCore import QTimer
        # Defer everything significantly to ensure app loop is running
        QTimer.singleShot(100, self.load_dependencies)

    def load_dependencies(self):
        """
        Load services and authenticate.
        """
        try:
            self.app.processEvents()

            # Import heavy dependencies here
            from core.dependency_container import DependencyContainer
            from controllers.theme_controller import ThemeController

            # Setup dependency injection container
            self.container = DependencyContainer(self.app)
            self.app.processEvents()

            # Load theme
            self._load_theme()
            
            # 1. ONLINE ACTIVATION CHECK
            # This will show the "Beautiful" Online Login Dialog if needed
            if not self._check_license():
                sys.exit(0)
                return
            
            # 2. LOCAL STAFF LOGIN
            self.show_login()

        except Exception as e:
            print(f"CRITICAL INIT ERROR: {e}")
            import traceback
            traceback.print_exc()

    def _check_license(self) -> bool:
        """
        Check for valid license. If missing/invalid, show activation dialog.
        Returns True if licensed, False if user cancelled/failed.
        """
        from services.license_service import LicenseService
        from views.dialogs.license_dialog import OnlineLoginDialog
        
        # SECURITY: Ensure we are running in a secure context if frozen
        if getattr(sys, 'frozen', False):
             # verify integrity if needed
             pass

        service = LicenseService()
        
        # Loop until valid license or user cancels
        while True:
            result = service.check_online_status()
            if result['valid']:
                # Valid license found
                print(f"✅ License Valid: {result.get('details', {}).get('name', 'User')}")
                return True
            
            print(f"⚠️ License Check Failed: {result['message']}")
            
            # Show Login Dialog (for activation)
            dialog = OnlineLoginDialog()
            if dialog.exec():
                continue
            else:
                return False

    def show_login(self):
        """
        Display the Local Login Dialog for staff access.
        """
        from views.auth.local_login_dialog import LocalLoginDialog
        from views.main_window import MainWindow

        # Handle Logout: If current window is MainWindow, close it first
        if self.current_window and isinstance(self.current_window, MainWindow):
            # Prevent app from quitting when we close the main window
            self.app.setQuitOnLastWindowClosed(False)
            self.current_window.close()
            self.current_window = None
            self.main_window = None
        
        # We need auth service
        auth_service = self.container.auth_service
        
        dialog = LocalLoginDialog(auth_service)
        if dialog.exec():
            # Login Success
            user = dialog.user
            self.show_main_window(user)
        else:
            # User cancelled local login
            sys.exit(0)
            
    def _initialize_auth(self):
        """Deprecated/Replaced by show_login logic"""
        pass

    def _start_preloading(self):
        """Deprecated - handled in load_dependencies now"""
        pass
    
    def _preload_step_1(self):
        """Deprecated - handled in load_dependencies now"""
        pass
    
    def _load_theme(self):
        """
        Load the application theme.
        
        Uses the theme controller from the dependency container to load
        the user's saved theme preference.
        """
        theme_controller = self.container.theme_controller
        theme_controller.load_theme(theme_controller.current_theme)

    def _preload_step_2(self):
        """Deprecated - handled in load_dependencies now"""
        pass

    def _preload_step_3(self):
        """Deprecated - handled in load_dependencies now"""
        pass

    def _preload_step_4(self):
        """Deprecated - handled in load_dependencies now"""
        pass
    
    def _preload_main_window(self):
        """
        DEPRECATED: Replaced by stepped preloading with progress updates.
        Kept for backward compatibility.
        """
        pass
    
    def show_main_window(self, user):
        """
        Display the main application window after successful login.
        
        Performs the following:
        1. Closes the login window
        2. Loads user's language preference
        3. Creates and displays the main window
        4. Connects logout signal
        
        Args:
            user: Authenticated user object
        """
        # Lazy import to avoid circular dependencies
        from views.main_window import MainWindow
        
        if self.current_window and isinstance(self.current_window, MainWindow):
            self.current_window.raise_()
            self.current_window.activateWindow()
            return

        # Close current window (login)
        if self.current_window:
            self.current_window.close()
        
        # Load user's language preference
        self._load_user_language(user)
        
        # Create and configure main window
        self.main_window = MainWindow(user, self.container)
        self.main_window.logout_requested.connect(self.show_login)
        
        # Update current window reference and show
        self.current_window = self.main_window
        self.current_window.show()
        
        # Now that main window is shown, enable quit on close
        self.app.setQuitOnLastWindowClosed(True)
    
    def _load_user_language(self, user):
        """
        Load the user's language preference.
        
        Retrieves the user's saved language setting and applies it
        before creating the main window.
        
        Args:
            user: User object with settings
        """
        settings = self.container.settings_service.get_user_settings(user.id)
        saved_language = settings.get('language', 'en')  # Default to 'en' language code
        language_manager.load_language(saved_language)
        
        # Save to QSettings so Login screen uses it next time
        from config.config_manager import SETTINGS_ORGANIZATION, SETTINGS_APPLICATION
        q_settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
        q_settings.setValue("system/language", saved_language)
    
    def on_login_success(self, user):
        """
        Legacy handler for successful login.
        
        Note: This method is kept for backward compatibility but is not
        currently used. The show_main_window method is connected directly
        to the login_success signal.
        
        Args:
            user: Authenticated user object
            
        Deprecated:
            Use show_main_window instead
        """
        from views.main_window import MainWindow
        
        if hasattr(self, 'main_window'):
            self.main_window.close()
        
        self.main_window = MainWindow(user, self.container)
        self.main_window.show()
        
        if hasattr(self, 'login_view'):
            self.login_view.hide()


def run():
    """
    Run the MSA application.
    
    Creates an MSA instance and starts the Qt event loop.
    This is a convenience function for running the application
    without going through the main.py entry point.
    
    Returns:
        int: Application exit code
    """
    auth_app = MSA()
    return sys.exit(auth_app.app.exec())


if __name__ == "__main__":
    run()