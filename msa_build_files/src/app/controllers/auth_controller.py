from PySide6.QtCore import Signal, QObject, QSettings
from config.config import SETTINGS_ORGANIZATION, SETTINGS_APPLICATION
from interfaces.iauth_service import IAuthService
from interfaces.irole_service import IRoleService
from views.auth.login import LoginView
from views.auth.register import RegisterView
from views.dialogs.forgot_password_dialog import ForgotPasswordDialog
from utils.validation.message_handler import MessageHandler

class AuthController(QObject):
    login_success = Signal(object)  # Emits User object when login succeeds
    
    def __init__(self, auth_service: IAuthService, role_service: IRoleService, login_view=None):
        super().__init__()
        if not isinstance(auth_service, IAuthService):
            raise ValueError("auth_service must implement IAuthService")
        if not isinstance(role_service, IRoleService):
            raise ValueError("role_service must implement IRoleService")
            
        self.auth_service = auth_service
        self.role_service = role_service
        
        # Initialize views
        self.login_view = login_view if login_view else LoginView()
        self.register_view = RegisterView()
        
        # Connect signals
        self.setup_connections()
    
    def setup_connections(self):
        """Connect all signals and slots"""
        self.login_view.login_attempt.connect(self.handle_login)
        self.login_view.register_requested.connect(self.show_register)
        self.login_view.forgot_password_requested.connect(self.show_forgot_password)
        self.register_view.register_attempt.connect(self.handle_register)
        self.register_view.back_to_login.connect(self.show_login)
    
    def show_login(self):
        """Show login view and hide register view"""
        self.register_view.hide()
        self.login_view.show()
        self.login_view.clear_form()
    
    def show_register(self):
        """Show register view and hide login view"""
        self.login_view.hide()
        self.register_view.show()
        self.register_view.clear_form()

    def show_forgot_password(self):
        """Show forgot password dialog"""
        dialog = ForgotPasswordDialog(self.login_view)
        dialog.exec()
    
    def handle_login(self, username: str, password: str, remember_me: bool = False):
        """Handle login attempt"""
        success, result = self.auth_service.login_user(username, password)
        
        if success:
            # Login successful - emit immediately (no animation needed)
            # Login successful - emit immediately (no animation needed)
            
            # Save "Remember Me" preference
            settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
            if remember_me:
                settings.setValue("auth/remember_username", username)
                settings.setValue("auth/remember_password", password)
                settings.setValue("auth/remember_me", True)
            else:
                settings.remove("auth/remember_username")
                settings.remove("auth/remember_password")
                settings.setValue("auth/remember_me", False)

            user = result
            self.login_success.emit(user)
            self.login_view.clear_form()
            self.login_view.hide()
        else:
            error_message = result
            MessageHandler.show_error(self.login_view, "Error", error_message)
            self.login_view.reset_ui()
    
    def handle_register(self, username: str, email: str, password: str):
        """Handle registration attempt"""
        success, message = self.auth_service.register_user(username, email, password)
        
        if success:
            MessageHandler.show_success(self.register_view, "Success", message)
            self.register_view.clear_form()
            self.register_view.back_to_login.emit()
            
        else:
            MessageHandler.show_error(self.register_view, "Error", message)