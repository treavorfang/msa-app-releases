# src/app/views/auth/login.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QSpacerItem, QSizePolicy, QFrame, QCheckBox
)
from PySide6.QtCore import Signal, Qt, QTimer, QSettings
from PySide6.QtGui import QAction, QPixmap, QPainter, QPainterPath, QIcon, QShowEvent
from utils.validation.message_handler import MessageHandler

from config.config import APP_SHORT_NAME, APP_VERSION, ICON_PATHS, SETTINGS_ORGANIZATION, SETTINGS_APPLICATION
from utils.language_manager import language_manager
from core.event_bus import EventBus
from core.events import LanguageContextChangedEvent

class LoginView(QWidget):
    login_attempt = Signal(str, str, bool)  # username, password, remember_me
    register_requested = Signal()
    forgot_password_requested = Signal()  # New Signal
    
    def __init__(self, settings_prefix="auth"):
        super().__init__()
        self.lm = language_manager
        self.settings_prefix = settings_prefix
        self.password_visible = False # Track password visibility state
        self.setWindowTitle(f"{APP_SHORT_NAME} | {APP_VERSION}")
        # self.setFixedSize(420, 680)  # Removed fixed size for responsiveness
        self.setObjectName("loginView")
        self.setup_ui()
        EventBus.subscribe(LanguageContextChangedEvent, self.update_language)

    def update_language(self, event=None):
        """Update UI text when language changes"""
        # We need to recreate the UI or update every label. 
        # Recreating is safer/cleaner for this simple view.
        # But for now, let's just update the known labels if we kept references, 
        # OR we just call setup_ui again on a clean slate? 
        # setup_ui adds widgets to layout. Calling it again would duplicate widgets.
        # So we should clear the layout first.
        
        # However, for Login, the language is usually set BEFORE login.
        # If user runs 'main.py' and language is loaded from config, it should work.
        # If user somehow changes language while ON login screen (not possible currently via UI), it would matter.
        pass
    
    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(20)
        
        # Banner Image
        banner_label = QLabel()
        banner_label.setAlignment(Qt.AlignCenter)
        # banner_label.setMaximumHeight(220) # Allow dynamic height based on image aspect ratio
        
        banner_path = ICON_PATHS.get('login_banner')
        if banner_path:
            pixmap = QPixmap(banner_path)
            if not pixmap.isNull():
                target_width = 320
                
                # Scale to WIDTH (Keep Aspect Ratio)
                # This ensures the image isn't distorted and fills the width
                scaled_pixmap = pixmap.scaledToWidth(target_width, Qt.SmoothTransformation)
                
                final_w = scaled_pixmap.width()
                final_h = scaled_pixmap.height()
                
                final_pixmap = QPixmap(final_w, final_h)
                final_pixmap.fill(Qt.transparent)
                
                # Draw rounded corners on the exact image size
                radius = 15
                painter = QPainter(final_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setRenderHint(QPainter.SmoothPixmapTransform)
                
                path = QPainterPath()
                path.addRoundedRect(0, 0, final_w, final_h, radius, radius)
                painter.setClipPath(path)
                
                painter.drawPixmap(0, 0, scaled_pixmap)
                painter.end()
                
                banner_label.setPixmap(final_pixmap)
                banner_label.setFixedHeight(final_h) # Set label height to matches image exactly
            else:
                # Fallback text
                banner_label.setText("MSA")
                banner_label.setStyleSheet("font-size: 38px; font-weight: 600; letter-spacing: 3px;")
                banner_label.setFixedHeight(100)
        else:
             banner_label.setText("MSA")
             banner_label.setStyleSheet("font-size: 38px; font-weight: 600; letter-spacing: 3px;")
             banner_label.setFixedHeight(100)
        
        layout.addWidget(banner_label)
        layout.addSpacing(15)
        
        # Username field
        self.username_label = QLabel(self.lm.get("Auth.username_label", "Username"))
        self.username_label.setObjectName("fieldLabel")
        layout.addWidget(self.username_label)
        layout.addSpacing(-12)  # Reduce spacing between label and input
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(self.lm.get("Auth.username_placeholder", "Enter username"))
        self.username_input.setMinimumHeight(42)
        self.username_input.setObjectName("authInput")
        layout.addWidget(self.username_input)
        
        # Password field with toggle button overlay
        password_label = QLabel(self.lm.get("Auth.password_placeholder", "Password"))
        password_label.setObjectName("fieldLabel")
        layout.addWidget(password_label)
        layout.addSpacing(-12)  # Reduce spacing between label and input
        
        # Use helper for password block
        self.password_container, self.password_input, self.toggle_password_btn = \
            self._create_password_block(
                "Auth.password_placeholder", "Enter password",
                self.on_login_clicked # Optional: trigger generic check if needed, or leave None
            )
        # Re-attach specific enter key behavior for login
        # Connect Enter key to login action
        self.password_input.returnPressed.connect(self.on_login_clicked)

        layout.addWidget(self.password_container)
        
        # Remember Me and Forgot Password Row
        options_layout = QHBoxLayout()
        options_layout.setContentsMargins(0, 0, 0, 0)
        
        self.remember_me_cb = QCheckBox(self.lm.get("Auth.remember_me", "Remember Me"))
        self.remember_me_cb.setObjectName("rememberMe_cb")
        self.remember_me_cb.setCursor(Qt.PointingHandCursor)
        self.remember_me_cb.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                color: #64748B;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #CBD5E1;
            }
            QCheckBox::indicator:checked {
                background-color: #3B82F6;
                border-color: #3B82F6;
                image: url(static/icons/check.png); /* Optional: if you have a check icon, or rely on native style */
            }
        """)
        options_layout.addWidget(self.remember_me_cb)
        
        options_layout.addStretch() # Spacer between them
        
        # Forgot password link
        forgot_pw = QLabel(f"<a href='forgot' style='color: #3B82F6; text-decoration: none;'>{self.lm.get('Auth.forgot_password', 'Forgot password?')}</a>")
        forgot_pw.setAlignment(Qt.AlignRight)
        forgot_pw.setObjectName("linkLabel")
        forgot_pw.setOpenExternalLinks(False)
        forgot_pw.linkActivated.connect(lambda _url: self.forgot_password_requested.emit())
        options_layout.addWidget(forgot_pw)

        layout.addLayout(options_layout)

        # Spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Login button
        self.login_btn = QPushButton(self.lm.get("Auth.login_button", "Sign In"))
        self.login_btn.setMinimumHeight(44)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setObjectName("primaryButton")
        self.login_btn.clicked.connect(self.on_login_clicked)
        layout.addWidget(self.login_btn)
        
        # Register button (Hidden by default, shown for Online Mode)
        self.register_btn = QPushButton(self.lm.get("Auth.register_link", "Create Account"))
        self.register_btn.setMinimumHeight(44)
        self.register_btn.setObjectName("secondaryButton")
        self.register_btn.clicked.connect(self.register_requested.emit)
        # Register Container (Button + Divider)
        self.register_container = QWidget()
        self.register_btn_layout = QVBoxLayout(self.register_container)
        self.register_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.register_btn_layout.setSpacing(12)
        
        # Divider
        divider = QHBoxLayout()
        line1 = QFrame(); line1.setFrameShape(QFrame.HLine); line1.setObjectName("dividerLine")
        or_lbl = QLabel(self.lm.get("Common.or", "or")); or_lbl.setObjectName("dividerText"); or_lbl.setAlignment(Qt.AlignCenter)
        line2 = QFrame(); line2.setFrameShape(QFrame.HLine); line2.setObjectName("dividerLine")
        divider.addWidget(line1, 1); divider.addWidget(or_lbl, 0); divider.addWidget(line2, 1)
        
        self.register_btn_layout.addLayout(divider)
        self.register_btn_layout.addWidget(self.register_btn)
        
        # Add container to main layout
        layout.addWidget(self.register_container)
        
        self.setLayout(layout)

    def set_register_visible(self, visible: bool):
        """Show/Hide register button and divider"""
        self.register_container.setVisible(visible)

    
    def _toggle_password_visibility(self):
        """Toggle password visibility"""
        self.password_visible = not self.password_visible
        if self.password_visible:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_password_btn.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setText("👁")
    
    def on_login_clicked(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            MessageHandler.show_error(self, self.lm.get("Common.error", "Error"), self.lm.get("Auth.invalid_credentials", "Please enter both username and password"))
            return
        
        self.login_attempt.emit(username, password, self.remember_me_cb.isChecked())
    
    def clear_form(self):
        self.username_input.clear()
        self.password_input.clear()
        self.password_visible = False
        self.password_input.setEchoMode(QLineEdit.Password)
        self.toggle_password_btn.setText("👁")
        self.remember_me_cb.setChecked(False)

    
    def reset_ui(self):
        """Reset UI state after failed login or error"""
        self.username_input.setEnabled(True)
        self.password_input.setEnabled(True)
        self.login_btn.setEnabled(True)
        self.login_btn.setText(self.lm.get("Auth.login_button", "Sign In"))

    def load_settings(self):
        """Load remembered username if enabled"""
        settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
        remember_me = settings.value(f"{self.settings_prefix}/remember_me", False, type=bool)
        
        if remember_me:
            username = settings.value(f"{self.settings_prefix}/remember_username", "")
            password = settings.value(f"{self.settings_prefix}/remember_password", "")
            
            if username:
                self.username_input.setText(username)
                
            if password:
                self.password_input.setText(password)
                
            self.remember_me_cb.setChecked(True)
            
            # If both are present, maybe focus login button or just leave it
            if username and password:
                self.login_btn.setFocus()
            elif username:
                self.password_input.setFocus()

    def showEvent(self, event: QShowEvent):
        """Handle window show event"""
        super().showEvent(event)
        self.load_settings()

    def closeEvent(self, event):
        """Handle window close event"""
        # Only quit if this is a user-initiated close (clicking X)
        # Programmatic closes (like transitioning to main window) are usually not spontaneous?
        # Actually, self.close() creates a non-spontaneous event.
        # Window manager close is spontaneous.
        if event.spontaneous():
            from PySide6.QtWidgets import QApplication
            QApplication.instance().quit()
        super().closeEvent(event)

    def _create_password_block(self, placeholder_key, default_placeholder, change_callback=None):
        """Helper to create consistent password fields with toggle buttons"""
        container = QWidget()
        container.setFixedHeight(42)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        input_field = QLineEdit()
        input_field.setPlaceholderText(self.lm.get(placeholder_key, default_placeholder))
        input_field.setEchoMode(QLineEdit.Password)
        input_field.setMinimumHeight(42)
        input_field.setObjectName("authInput")
        if change_callback:
            # For login, we might not assume textChanged; but helper supports it
            pass
            
        toggle_btn = QPushButton("👁")
        toggle_btn.setFixedSize(35, 38)
        toggle_btn.setCursor(Qt.PointingHandCursor)
        toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 16px;
                padding: 0;
                color: #555;
            }
            QPushButton:hover {
                background: rgba(0, 0, 0, 0.05);
                border-radius: 4px;
            }
        """)
        toggle_btn.clicked.connect(lambda checked=False, inp=input_field, btn=toggle_btn: self._toggle_visibility(inp, btn))
        
        layout.addWidget(input_field)
        layout.addWidget(toggle_btn)
        layout.setAlignment(toggle_btn, Qt.AlignRight | Qt.AlignVCenter)
        
        return container, input_field, toggle_btn

    def _toggle_visibility(self, input_field, btn):
        self.password_visible = not self.password_visible # Keep state for logic if needed elsewhere
        if input_field.echoMode() == QLineEdit.Password:
            input_field.setEchoMode(QLineEdit.Normal)
            btn.setText("🙈")
        else:
            input_field.setEchoMode(QLineEdit.Password)
            btn.setText("👁")