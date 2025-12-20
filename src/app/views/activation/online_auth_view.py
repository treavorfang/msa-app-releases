from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QStackedWidget, QCheckBox, QMessageBox,
    QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPainter, QPainterPath

from services.license_service import LicenseService
from config.config import ICON_PATHS
from utils.language_manager import language_manager

class OnlineLoginView(QWidget):
    login_requested = Signal(str, str) # email, password
    register_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.lm = language_manager
        self.password_visible = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Banner/Logo
        banner_label = QLabel()
        banner_label.setAlignment(Qt.AlignCenter)
        banner_label.setText("MSA Cloud")
        banner_label.setStyleSheet("font-size: 32px; font-weight: 700; color: #3B82F6; letter-spacing: 2px;")
        banner_label.setFixedHeight(80)
        layout.addWidget(banner_label)
        
        layout.addSpacing(10)
        
        # Info Text
        info = QLabel("Sign in to activate your device.")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #64748B; font-size: 14px;")
        layout.addWidget(info)
        layout.addSpacing(10)

        # Email
        email_label = QLabel("Email Address")
        email_label.setObjectName("fieldLabel")
        layout.addWidget(email_label)
        layout.addSpacing(-12)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("name@company.com")
        self.email_input.setMinimumHeight(42)
        self.email_input.setObjectName("authInput")
        layout.addWidget(self.email_input)

        # Password
        pass_label = QLabel("Password")
        pass_label.setObjectName("fieldLabel")
        layout.addWidget(pass_label)
        layout.addSpacing(-12)

        # Password container
        pass_container = QWidget()
        pass_container.setFixedHeight(42)
        pass_layout = QHBoxLayout(pass_container)
        pass_layout.setContentsMargins(0, 0, 0, 0)
        pass_layout.setSpacing(0)
        
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Enter password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setMinimumHeight(42)
        self.pass_input.setObjectName("authInput")
        self.pass_input.returnPressed.connect(self.on_login)
        
        self.toggle_btn = QPushButton("👁")
        self.toggle_btn.setFixedSize(35, 38)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setStyleSheet("border: none; background: transparent;")
        self.toggle_btn.clicked.connect(self.toggle_password)

        pass_layout.addWidget(self.pass_input)
        pass_layout.addWidget(self.toggle_btn)
        layout.addWidget(pass_container)

        # Login Button
        layout.addSpacing(10)
        self.login_btn = QPushButton("Sign In & Activate")
        self.login_btn.setMinimumHeight(45)
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setObjectName("primaryButton")
        self.login_btn.clicked.connect(self.on_login)
        layout.addWidget(self.login_btn)

        # Divider
        div_layout = QHBoxLayout()
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setObjectName("dividerLine")
        or_lbl = QLabel("or")
        or_lbl.setObjectName("dividerText")
        or_lbl.setAlignment(Qt.AlignCenter)
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setObjectName("dividerLine")
        
        div_layout.addWidget(line1)
        div_layout.addWidget(or_lbl)
        div_layout.addWidget(line2)
        layout.addLayout(div_layout)

        # Create Account
        reg_btn = QPushButton("Create New Account")
        reg_btn.setMinimumHeight(45)
        reg_btn.setObjectName("secondaryButton")
        reg_btn.clicked.connect(self.register_clicked.emit)
        layout.addWidget(reg_btn)
        
        layout.addStretch()
        
        # HWID Footer
        self.license = LicenseService()
        hwid = self.license.get_machine_fingerprint()
        hwid_lbl = QLabel(f"Device ID: {hwid}")
        hwid_lbl.setStyleSheet("color: #94A3B8; font-size: 10px;")
        hwid_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(hwid_lbl)

        self.setLayout(layout)

    def toggle_password(self):
        self.password_visible = not self.password_visible
        if self.password_visible:
            self.pass_input.setEchoMode(QLineEdit.Normal)
            self.toggle_btn.setText("🙈")
        else:
            self.pass_input.setEchoMode(QLineEdit.Password)
            self.toggle_btn.setText("👁")

    def on_login(self):
        email = self.email_input.text().strip()
        pwd = self.pass_input.text().strip()
        if not email or not pwd:
            QMessageBox.warning(self, "Validation", "Please enter Email and Password")
            return
        self.login_requested.emit(email, pwd)


class OnlineRegisterView(QWidget):
    register_requested = Signal(str, str, str, str, str, str) # username, email, password, phone, city, country
    back_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(10)

        title = QLabel("Create Account")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: #3B82F6;")
        layout.addWidget(title)
        
        sub = QLabel("Register your license online")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #64748B;")
        layout.addWidget(sub)
        
        # Scroll area if needed? No, let's keep it compact or use scroll if it gets too tall.
        # But we are inside a dialog of fixed size potentially. 
        # Making it a scrollable form is safer.
        
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)
        
        # Username
        form_layout.addWidget(QLabel("Username *"))
        self.username = QLineEdit()
        self.username.setPlaceholderText("Choose username")
        self.username.setMinimumHeight(35)
        form_layout.addWidget(self.username)

        # Email
        form_layout.addWidget(QLabel("Email *"))
        self.email = QLineEdit()
        self.email.setPlaceholderText("email@example.com")
        self.email.setMinimumHeight(35)
        form_layout.addWidget(self.email)
        
        # Phone
        form_layout.addWidget(QLabel("Phone *"))
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("+1 234 ...")
        self.phone.setMinimumHeight(35)
        form_layout.addWidget(self.phone)

        # City / Country Row
        loc_row = QHBoxLayout()
        city_col = QVBoxLayout()
        city_col.setSpacing(2)
        city_col.addWidget(QLabel("City"))
        self.city = QLineEdit()
        self.city.setPlaceholderText("Yangon")
        self.city.setMinimumHeight(35)
        city_col.addWidget(self.city)
        
        country_col = QVBoxLayout()
        country_col.setSpacing(2)
        country_col.addWidget(QLabel("Country"))
        self.country = QLineEdit()
        self.country.setPlaceholderText("Myanmar")
        self.country.setMinimumHeight(35)
        country_col.addWidget(self.country)
        
        loc_row.addLayout(city_col)
        loc_row.addLayout(country_col)
        form_layout.addLayout(loc_row)

        # Password
        form_layout.addWidget(QLabel("Password *"))
        self.pwd = QLineEdit()
        self.pwd.setPlaceholderText("Password")
        self.pwd.setEchoMode(QLineEdit.Password)
        self.pwd.setMinimumHeight(35)
        form_layout.addWidget(self.pwd)

        # Confirm
        form_layout.addWidget(QLabel("Confirm Password *"))
        self.cpwd = QLineEdit()
        self.cpwd.setPlaceholderText("Confirm Password")
        self.cpwd.setEchoMode(QLineEdit.Password)
        self.cpwd.setMinimumHeight(35)
        form_layout.addWidget(self.cpwd)

        layout.addLayout(form_layout)
        layout.addSpacing(10)
        
        # Register Btn
        self.btn = QPushButton("Register Device")
        self.btn.setMinimumHeight(45)
        self.btn.setObjectName("primaryButton")
        self.btn.clicked.connect(self.on_register)
        layout.addWidget(self.btn)

        # Back
        back = QPushButton("← Back to Login")
        back.setFlat(True)
        back.setStyleSheet("color: #64748B; padding: 10px;")
        back.setCursor(Qt.PointingHandCursor)
        back.clicked.connect(self.back_clicked.emit)
        layout.addWidget(back)

        layout.addStretch()
        self.setLayout(layout)

    def on_register(self):
        username = self.username.text().strip()
        email = self.email.text().strip()
        phone = self.phone.text().strip()
        p1 = self.pwd.text()
        p2 = self.cpwd.text()
        city = self.city.text().strip()
        country = self.country.text().strip()
        
        if not all([username, email, phone, p1, p2]):
            QMessageBox.warning(self, "Error", "Please fill all required fields")
            return
            
        if p1 != p2:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return
            
        self.register_requested.emit(username, email, p1, phone, city, country)
