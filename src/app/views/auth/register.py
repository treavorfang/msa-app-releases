# src/app/views/auth/register.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QSpacerItem, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from utils.validation.message_handler import MessageHandler
from utils.validation.input_validator import InputValidator
from config.config import APP_SHORT_NAME, APP_VERSION
from utils.language_manager import language_manager

class RegisterView(QWidget):
    register_attempt = Signal(str, str, str, str, str, str) # username, email, password, phone, city, country
    back_to_login = Signal()
    
    def __init__(self):
        super().__init__()
        self.lm = language_manager
        self.setWindowTitle(f"{APP_SHORT_NAME} | {APP_VERSION}")
        # self.setFixedSize(420, 780) # Removed fixed size for responsiveness
        self.setObjectName("registerView")
        self.setup_ui()
    
    def setup_ui(self):
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 20, 50, 20) # Reduced top/bottom margin
        layout.setSpacing(12) # Reduced spacing
        
        # Logo/Title section
        title_container = QVBoxLayout()
        title_container.setSpacing(6)
        
        # App name
        app_name = QLabel("MSA")
        app_name.setAlignment(Qt.AlignCenter)
        app_name.setObjectName("appLogo")
        app_name.setStyleSheet("font-size: 38px; font-weight: 600; letter-spacing: 3px;")
        # title_container.addWidget(app_name) # Removed to prevent cutoff
        
        # Subtitle
        subtitle = QLabel(self.lm.get("Auth.create_account_title", "Create your account"))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("appSubtitle")
        title_container.addWidget(subtitle)
        
        layout.addLayout(title_container)
        layout.addSpacing(5)
        
        # Username field
        username_label = QLabel(self.lm.get("Auth.username_label", "Username *"))
        username_label.setObjectName("fieldLabel")
        layout.addWidget(username_label)
        layout.addSpacing(-8)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(self.lm.get("Auth.username_placeholder", "Choose a username"))
        self.username_input.setMinimumHeight(40)
        self.username_input.setObjectName("authInput")
        layout.addWidget(self.username_input)
        
        # Email field
        email_label = QLabel(self.lm.get("Auth.email_label", "Email *"))
        email_label.setObjectName("fieldLabel")
        layout.addWidget(email_label)
        layout.addSpacing(-8)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText(self.lm.get("Auth.email_placeholder_text", "your@email.com"))
        self.email_input.setMinimumHeight(40)
        self.email_input.setObjectName("authInput")
        self.email_input.textChanged.connect(self._validate_email_field)
        layout.addWidget(self.email_input)

        # Phone field
        phone_label = QLabel(self.lm.get("Auth.phone_label", "Phone *"))
        phone_label.setObjectName("fieldLabel")
        layout.addWidget(phone_label)
        layout.addSpacing(-8)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText(self.lm.get("Auth.phone_placeholder", "+1 234 567 890"))
        self.phone_input.setMinimumHeight(40)
        self.phone_input.setObjectName("authInput")
        layout.addWidget(self.phone_input)

        # City & Country Row
        loc_layout = QHBoxLayout()
        loc_layout.setSpacing(10)
        
        # City
        city_container = QWidget()
        city_v = QVBoxLayout(city_container)
        city_v.setContentsMargins(0,0,0,0)
        city_v.setSpacing(4)
        city_lbl = QLabel(self.lm.get("Auth.city_label", "City (Optional)"))
        city_lbl.setObjectName("fieldLabel")
        city_lbl.setStyleSheet("font-size: 11px;")
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText(self.lm.get("Auth.city_placeholder", "Yangon"))
        self.city_input.setMinimumHeight(40)
        self.city_input.setObjectName("authInput")
        city_v.addWidget(city_lbl)
        city_v.addWidget(self.city_input)
        
        # Country
        country_container = QWidget()
        country_v = QVBoxLayout(country_container)
        country_v.setContentsMargins(0,0,0,0)
        country_v.setSpacing(4)
        country_lbl = QLabel(self.lm.get("Auth.country_label", "Country (Optional)"))
        country_lbl.setObjectName("fieldLabel")
        country_lbl.setStyleSheet("font-size: 11px;")
        self.country_input = QLineEdit()
        self.country_input.setPlaceholderText(self.lm.get("Auth.country_placeholder", "Myanmar"))
        self.country_input.setMinimumHeight(40)
        self.country_input.setObjectName("authInput")
        country_v.addWidget(country_lbl)
        country_v.addWidget(self.country_input)
        
        loc_layout.addWidget(city_container)
        loc_layout.addWidget(country_container)
        
        layout.addLayout(loc_layout)

        # Password field
        password_label = QLabel(self.lm.get("Auth.password_label", "Password *"))
        password_label.setObjectName("fieldLabel")
        layout.addWidget(password_label)
        layout.addSpacing(-8)
        
        self.password_container, self.password_input, self.toggle_password_btn = \
            self._create_password_block(
                "Auth.password_placeholder_text", "Create password", 
                self.update_password_strength
            )
        layout.addWidget(self.password_container)
        
        # Password strength
        self.strength_label = QLabel("")
        self.strength_label.setObjectName("statusLabel")
        layout.addWidget(self.strength_label)

        # Confirm password field
        confirm_label = QLabel(self.lm.get("Auth.confirm_password_label", "Confirm Password *"))
        confirm_label.setObjectName("fieldLabel")
        layout.addWidget(confirm_label)
        layout.addSpacing(-8)
        
        self.confirm_container, self.confirm_input, self.toggle_confirm_btn = \
            self._create_password_block(
                "Auth.confirm_password_placeholder", "Confirm password", 
                self.update_password_match
            )
        layout.addWidget(self.confirm_container)

        # Password match indicator
        self.match_label = QLabel("")
        self.match_label.setObjectName("statusLabel")
        layout.addWidget(self.match_label)
        
        # Spacer
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Register button
        self.register_btn = QPushButton(self.lm.get("Auth.register_button", "Create Account"))
        self.register_btn.setMinimumHeight(44)
        self.register_btn.setCursor(Qt.PointingHandCursor)
        self.register_btn.setObjectName("primaryButton")
        self.register_btn.clicked.connect(self.on_register_clicked)
        layout.addWidget(self.register_btn)
        
        # Back to login button
        back_btn = QPushButton(self.lm.get("Auth.back_to_login", "← Back to Sign In"))
        back_btn.setMinimumHeight(44)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setObjectName("secondaryButton")
        back_btn.clicked.connect(self.back_to_login.emit)
        layout.addWidget(back_btn)
        
        self.setLayout(layout)
    
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
        input_field.setMinimumHeight(40)
        input_field.setObjectName("authInput")
        if change_callback:
            input_field.textChanged.connect(change_callback)
            
        toggle_btn = QPushButton("👁")
        toggle_btn.setFixedSize(35, 38)
        toggle_btn.setCursor(Qt.PointingHandCursor)
        toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 16px;
                padding: 0;
            }
            QPushButton:hover {
                background: rgba(0, 0, 0, 0.05);
                border-radius: 4px;
            }
        """)
        # We need to bind the specific input and button to the toggle logic
        # Using lambda with default args to capture current values
        toggle_btn.clicked.connect(lambda checked=False, inp=input_field, btn=toggle_btn: self._toggle_visibility(inp, btn))
        
        layout.addWidget(input_field)
        layout.addWidget(toggle_btn)
        layout.setAlignment(toggle_btn, Qt.AlignRight | Qt.AlignVCenter)
        
        return container, input_field, toggle_btn

    def _toggle_visibility(self, input_field, btn):
        if input_field.echoMode() == QLineEdit.Password:
            input_field.setEchoMode(QLineEdit.Normal)
            btn.setText("🙈")
        else:
            input_field.setEchoMode(QLineEdit.Password)
            btn.setText("👁")
        
        # Password match indicator
        self.match_label = QLabel("")
        self.match_label.setObjectName("statusLabel")
        layout.addWidget(self.match_label)
        
        # Spacer
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Register button
        self.register_btn = QPushButton(self.lm.get("Auth.register_button", "Create Account"))
        self.register_btn.setMinimumHeight(44)
        self.register_btn.setCursor(Qt.PointingHandCursor)
        self.register_btn.setObjectName("primaryButton")
        self.register_btn.clicked.connect(self.on_register_clicked)
        layout.addWidget(self.register_btn)
        
        # Back to login button
        back_btn = QPushButton(self.lm.get("Auth.back_to_login", "← Back to Sign In"))
        back_btn.setMinimumHeight(44)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setObjectName("secondaryButton")
        back_btn.clicked.connect(self.back_to_login.emit)
        layout.addWidget(back_btn)
        
        self.setLayout(layout)
    
    def _toggle_password_visibility(self):
        """Toggle password visibility"""
        self.password_visible = not self.password_visible
        if self.password_visible:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_password_btn.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setText("👁")
    
    def _toggle_confirm_visibility(self):
        """Toggle confirm password visibility"""
        self.confirm_visible = not self.confirm_visible
        if self.confirm_visible:
            self.confirm_input.setEchoMode(QLineEdit.Normal)
            self.toggle_confirm_btn.setText("🙈")
        else:
            self.confirm_input.setEchoMode(QLineEdit.Password)
            self.toggle_confirm_btn.setText("👁")

    def _validate_email_field(self):
        email = self.email_input.text()
        if email:
            is_valid, _ = InputValidator.validate_email(email)
            # Don't override theme styling, just let validation happen in on_register_clicked
    
    def update_password_strength(self):
        password = self.password_input.text()
        
        if not password:
            self.strength_label.setText("")
            return
        
        complexity = InputValidator.validate_password_complexity(password)
        total_checks = len(complexity)
        passed_checks = sum(1 for is_valid, _ in complexity.values() if is_valid)
        strength_percent = (passed_checks / total_checks) * 100
        
        if strength_percent < 40:
            text = self.lm.get("Auth.strength_weak", "Strength: Weak")
            color = "#EF4444"  # Red
        elif strength_percent < 70:
            text = self.lm.get("Auth.strength_fair", "Strength: Fair")
            color = "#F59E0B"  # Orange
        elif strength_percent < 90:
            text = self.lm.get("Auth.strength_good", "Strength: Good")
            color = "#3B82F6"  # Blue
        else:
            text = self.lm.get("Auth.strength_strong", "Strength: Strong")
            color = "#10B981"  # Green
        
        self.strength_label.setText(text)
        self.strength_label.setStyleSheet(f"font-size: 11px; color: {color}; font-weight: 500;")
        self.update_password_match()
    
    def update_password_match(self):
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        
        if not password and not confirm:
            self.match_label.setText("")
            return
            
        if password and confirm:
            if password == confirm:
                self.match_label.setText(self.lm.get("Auth.passwords_match", "✓ Passwords match"))
                self.match_label.setStyleSheet("font-size: 11px; color: #10B981; font-weight: 500;")
            else:
                self.match_label.setText(self.lm.get("Auth.passwords_dont_match", "✗ Passwords don't match"))
                self.match_label.setStyleSheet("font-size: 11px; color: #EF4444; font-weight: 500;")
    
    def on_register_clicked(self):
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        city = self.city_input.text().strip()
        country = self.country_input.text().strip()
        
        # Required fields check
        if not all([username, email, password, confirm, phone]):
            MessageHandler.show_error(self, self.lm.get("Common.error", "Error"), self.lm.get("Auth.fill_all_fields", "Please fill in all required fields"))
            return
        
        if password != confirm:
            MessageHandler.show_error(self, self.lm.get("Common.error", "Error"), self.lm.get("Auth.passwords_mismatch", "Passwords do not match"))
            return
        
        email_valid, email_msg = InputValidator.validate_email(email)
        if not email_valid:
            MessageHandler.show_error(self, self.lm.get("Auth.invalid_email_title", "Invalid Email"), email_msg)
            return
        
        is_valid, message = InputValidator.validate_password(password)
        
        if is_valid and "Warning:" in message:
            result = MessageHandler.show_warning_confirm(
                self, 
                self.lm.get("Auth.security_warning_title", "Security Warning"), 
                f"{message}\n\n{self.lm.get('Auth.use_anyway_question', 'Do you want to use this password anyway?')}",
                self.lm.get("Auth.use_anyway", "Use Anyway"),
                self.lm.get("Auth.choose_different", "Choose Different Password")
            )
            if not result:
                return
        elif not is_valid:
            MessageHandler.show_error(self, self.lm.get("Auth.weak_password_title", "Weak Password"), message)
            return
        
        self.register_attempt.emit(username, email, password, phone, city, country)
    
    def clear_form(self):
        self.username_input.clear()
        self.email_input.clear()
        self.password_input.clear()
        self.confirm_input.clear()
        self.strength_label.setText("")
        self.match_label.setText("")
        self.password_visible = False
        self.confirm_visible = False
        self.password_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.toggle_password_btn.setText("👁")
        self.toggle_confirm_btn.setText("👁")

    def closeEvent(self, event):
        """Handle window close event"""
        if event.spontaneous():
            from PySide6.QtWidgets import QApplication
            QApplication.instance().quit()
        super().closeEvent(event)