from PySide6.QtWidgets import QDialog, QVBoxLayout, QMessageBox
from PySide6.QtCore import Qt
from views.auth.login import LoginView
from utils.language_manager import language_manager

class LocalLoginDialog(QDialog):
    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.user = None
        self.lm = language_manager
        
        self.setWindowTitle(self.lm.get("Auth.staff_login_title", "Staff Login"))
        self.setFixedSize(420, 680)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        
        self.setup_ui()

    def setup_ui(self):
        # Remove default padding to let the view fill the dialog
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # USE DISTINCT SETTINGS PREFIX
        # This prevents conflict with Online Activation (which uses default "auth")
        self.login_view = LoginView(settings_prefix="staff_local")
        
        # Hide registration for local staff login
        self.login_view.set_register_visible(False)
        self.login_view.username_label.setText(self.lm.get("Auth.username_label", "Username"))
        self.login_view.username_input.setPlaceholderText(self.lm.get("Auth.username_placeholder", "Enter Username"))
        
        # Connect signals
        self.login_view.login_attempt.connect(self.handle_login)
        self.login_view.forgot_password_requested.connect(self.handle_forgot_password)
        
        # Note: LoginView automatically loads settings on showEvent based on the prefix.
        
        layout.addWidget(self.login_view)

    def handle_login(self, username, password, remember_me):
        # Disable button during processing
        self.login_view.login_btn.setEnabled(False)
        self.login_view.login_btn.setText(self.lm.get("Auth.authenticating", "Authenticating..."))
        self.login_view.repaint()
        
        try:
            success, result = self.auth_service.login_user(username, password)
            
            if success:
                self.user = result
                
                # Handle Remember Me Logic (Standardized)
                from PySide6.QtCore import QSettings
                from config.config import SETTINGS_ORGANIZATION, SETTINGS_APPLICATION
                
                settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
                prefix = "staff_local"
                
                if remember_me:
                    settings.setValue(f"{prefix}/remember_me", True)
                    settings.setValue(f"{prefix}/remember_username", username)
                    # LoginView logic can load password if we save it, 
                    # but typically we only save username for security unless requested.
                    # Since the previous code supported password saving (implicitly via LoginView structure),
                    # we can choose to save it or not. 
                    # Let's save it to match previous behavior if LoginView supports auto-fill.
                    settings.setValue(f"{prefix}/remember_password", password)
                else:
                    settings.setValue(f"{prefix}/remember_me", False)
                    settings.remove(f"{prefix}/remember_username")
                self.accept()
            else:
                QMessageBox.warning(self, self.lm.get("Auth.login_failed_title", "Login Failed"), str(result))
        except Exception as e:
            QMessageBox.critical(self, self.lm.get("Common.error", "Error"), f"{self.lm.get('Common.unexpected_error', 'An unexpected error occurred')}: {str(e)}")
        finally:
            self.login_view.login_btn.setEnabled(True)
            self.login_view.login_btn.setText(self.lm.get("Auth.login_button", "Sign In"))

    def handle_forgot_password(self):
        QMessageBox.information(
            self, 
            self.lm.get("Auth.forgot_password_title", "Forgot Password"), 
            self.lm.get("Auth.contact_admin_reset", "Please contact your system administrator to reset your password.")
        )
