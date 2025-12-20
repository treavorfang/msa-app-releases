from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QHBoxLayout, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
                               QCheckBox)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QFont, QCursor

class ModernInput(QLineEdit):
    def __init__(self, placeholder="", parent=None, is_password=False):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        if is_password:
            self.setEchoMode(QLineEdit.Password)
        
        # Styles specific to the input
        self.setStyleSheet("""
            QLineEdit {
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 12px 16px;
                color: #ffffff;
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                selection-background-color: #3b82f6;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
                background: rgba(0, 0, 0, 0.4);
            }
            QLineEdit::placeholder {
                color: #64748b;
            }
        """)
        self.setMinimumHeight(45)

class ModernButton(QPushButton):
    def __init__(self, text, parent=None, is_primary=True):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(48)
        
        if is_primary:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3b82f6, stop:1 #2563eb);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    font-size: 15px;
                    font-weight: 600;
                    font-family: 'Inter', sans-serif;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #60a5fa, stop:1 #3b82f6);
                }
                QPushButton:pressed {
                    background: #1d4ed8;
                }
                QPushButton:disabled {
                    background: rgba(51, 65, 85, 0.5);
                    color: #94a3b8;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #94a3b8;
                    border: none;
                    text-align: left;
                    font-size: 13px;
                }
                QPushButton:hover {
                    color: #cbd5e1;
                    text-decoration: underline;
                }
            """)

class ModernLoginView(QWidget):
    login_requested = Signal(str, str) # email, password
    register_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # FORCE TRANSPARENT BACKGROUND
        self.setAttribute(Qt.WA_TranslucentBackground) 
        self.setStyleSheet("background: transparent;")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        # Add padding to ensure content isn't flush against the card edges (though card has padding too)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Logo Area
        logo_layout = QVBoxLayout()
        logo_layout.setSpacing(5)
        logo_label = QLabel("MSA")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("""
            font-size: 48px; 
            font-weight: 800; 
            color: #3b82f6;
            font-family: 'Inter', sans-serif;
        """)
        logo_sub = QLabel("Mobile Service Accounting")
        logo_sub.setAlignment(Qt.AlignCenter)
        logo_sub.setStyleSheet("color: #94a3b8; font-size: 14px; font-weight: 500;")
        
        logo_layout.addWidget(logo_label)
        logo_layout.addWidget(logo_sub)
        layout.addLayout(logo_layout)
        layout.addSpacing(15)

        # Inputs
        input_container = QVBoxLayout()
        input_container.setSpacing(5)
        
        lbl_email = QLabel("Email")
        lbl_email.setStyleSheet("color: #cbd5e1; font-size: 12px; font-weight: 600; margin-left: 4px;")
        self.email = ModernInput("Enter your email address")
        input_container.addWidget(lbl_email)
        input_container.addWidget(self.email)
        
        input_container.addSpacing(10)
        
        lbl_pass = QLabel("Password")
        lbl_pass.setStyleSheet("color: #cbd5e1; font-size: 12px; font-weight: 600; margin-left: 4px;")
        self.password = ModernInput("Enter password", is_password=True)
        input_container.addWidget(lbl_pass)
        input_container.addWidget(self.password)
        
        layout.addLayout(input_container)

        # Options Row
        opt_layout = QHBoxLayout()
        
        # Custom Checkbox Style
        self.remember_cb = QCheckBox("Remember Me")
        self.remember_cb.setCursor(Qt.PointingHandCursor)
        self.remember_cb.setStyleSheet("""
            QCheckBox { color: #94a3b8; font-size: 13px; spacing: 8px; background: transparent; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 1px solid #475569; background: rgba(0, 0, 0, 0.2); }
            QCheckBox::indicator:checked { background: #3b82f6; border-color: #3b82f6; } 
        """)
        
        forgot_btn = QPushButton("Forgot password?")
        forgot_btn.setCursor(Qt.PointingHandCursor)
        forgot_btn.setStyleSheet("border: none; background: transparent; color: #3b82f6; font-weight: 600; font-size: 13px;")
        
        opt_layout.addWidget(self.remember_cb)
        opt_layout.addStretch()
        opt_layout.addWidget(forgot_btn)
        layout.addLayout(opt_layout)

        layout.addSpacing(15)

        # Buttons
        self.login_btn = ModernButton("Sign in")
        self.login_btn.clicked.connect(self.on_login)
        layout.addWidget(self.login_btn)
        
        # Register Link
        reg_layout = QHBoxLayout()
        reg_layout.addStretch()
        reg_lbl = QLabel("Don't have an account?")
        reg_lbl.setStyleSheet("color: #94a3b8; font-size: 13px; background: transparent;")
        reg_btn = QPushButton("Create one")
        reg_btn.setCursor(Qt.PointingHandCursor)
        reg_btn.setStyleSheet("border: none; background: transparent; color: #3b82f6; font-weight: 600; font-size: 13px; margin-left: 4px;")
        reg_btn.clicked.connect(self.register_clicked.emit)
        
        reg_layout.addWidget(reg_lbl)
        reg_layout.addWidget(reg_btn)
        reg_layout.addStretch()
        layout.addLayout(reg_layout)
        
        layout.addStretch()

    def on_login(self):
        email = self.email.text().strip()
        pwd = self.password.text()
        if not email or not pwd:
            return 
        self.login_requested.emit(email, pwd)
        
    def reset_ui(self):
        self.login_btn.setText("Sign in")
        self.login_btn.setEnabled(True)


class ModernRegisterView(QWidget):
    register_requested = Signal(str, str, str, str, str, str) # username, email, pwd, phone, city, country
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(10, 0, 10, 0)

        # Header
        title = QLabel("Create Account")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #e2e8f0; font-family: 'Inter', sans-serif;")
        layout.addWidget(title)
        
        sub = QLabel("Register your license online")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        layout.addWidget(sub)
        
        layout.addSpacing(10)

        # Fields
        self.username = ModernInput("Username")
        layout.addWidget(self.username)
        
        self.email = ModernInput("Email Address")
        layout.addWidget(self.email)
        
        # Phone
        self.phone = ModernInput("Phone Number")
        layout.addWidget(self.phone)
        
        # City/Country
        row = QHBoxLayout()
        self.city = ModernInput("City")
        self.country = ModernInput("Country")
        row.addWidget(self.city)
        row.addWidget(self.country)
        layout.addLayout(row)
        
        self.pwd = ModernInput("Password", is_password=True)
        layout.addWidget(self.pwd)
        
        self.cpwd = ModernInput("Confirm Password", is_password=True)
        layout.addWidget(self.cpwd)

        layout.addSpacing(10)

        self.btn = ModernButton("Register Device")
        self.btn.clicked.connect(self.on_register)
        layout.addWidget(self.btn)

        # Back
        back_btn = QPushButton("← Back to Sign in")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #64748b; border: none; font-size: 13px; margin-top: 10px; }
            QPushButton:hover { color: #94a3b8; }
        """)
        back_btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(back_btn, 0, Qt.AlignCenter)
        
        layout.addStretch()

    def on_register(self):
        u = self.username.text().strip()
        e = self.email.text().strip()
        p = self.phone.text().strip()
        c = self.city.text().strip()
        co = self.country.text().strip()
        p1 = self.pwd.text()
        p2 = self.cpwd.text()
        
        if not all([u, e, p, c, co, p1, p2]):
            # Simple validation feedback
            return

        if p1 != p2:
            return

        self.register_requested.emit(u, e, p1, p, c, co)


class ModernPendingView(QWidget):
    back_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 40, 20, 40)
        
        icon = QLabel("⏳")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 60px; background: transparent;")
        layout.addWidget(icon)
        
        title = QLabel("Registration Successful")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #3b82f6; background: transparent;")
        layout.addWidget(title)
        
        msg = QLabel("Your account is pending approval.\nPlease contact support to activate your license.")
        msg.setAlignment(Qt.AlignCenter)
        msg.setWordWrap(True)
        msg.setStyleSheet("color: #cbd5e1; font-size: 15px; line-height: 1.5; background: transparent;")
        layout.addWidget(msg)
        
        layout.addSpacing(20)
        
        # Fake Contact Info (simplified for demo)
        contact = QLabel("Support: +959 123 456 789\nWeChat: MSASupport")
        contact.setAlignment(Qt.AlignCenter)
        contact.setStyleSheet("background: rgba(0, 0, 0, 0.2); padding: 15px; border-radius: 8px; color: #94a3b8; border: 1px solid rgba(255,255,255,0.1);")
        layout.addWidget(contact)
        
        layout.addStretch()
        
        btn = ModernButton("Back to Sign in")
        btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(btn)
