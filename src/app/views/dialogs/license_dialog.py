from PySide6.QtWidgets import (QDialog, QVBoxLayout, QStackedWidget, QMessageBox, QLabel, 
                               QFrame, QPushButton, QHBoxLayout, QApplication, QScrollArea, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QSize
from services.license_service import LicenseService
from views.auth.login import LoginView
from views.auth.register import RegisterView
from PySide6.QtCore import QThread

class AuthWorker(QThread):
    finished = Signal(dict)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"success": False, "valid": False, "message": str(e)})

class PendingApprovalView(QFrame):
    back_to_login = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setStyleSheet("""
            QFrame { background: transparent; }
            QLabel { color: #1E293B; font-size: 14px; }
            .Header { font-size: 24px; font-weight: bold; color: #3B82F6; margin-bottom: 10px; }
            .SubHeader { font-size: 16px; color: #64748B; margin-bottom: 20px; }
            .ContactCard { 
                background-color: #F1F5F9; 
                border-radius: 8px; 
                padding: 15px;
                border: 1px solid #E2E8F0;
            }
            .ContactLabel { font-weight: bold; color: #3B82F6; font-size: 13px; }
            .ContactValue { font-size: 15px; color: #0F172A; font-weight: 500; }
        """)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Icon/Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        
        icon_lbl = QLabel("⏳")  
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 48px;")
        header_layout.addWidget(icon_lbl)
        
        title = QLabel("Registration Successful")
        title.setProperty("class", "Header")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        
        subtitle = QLabel("Your account is pending approval.")
        subtitle.setProperty("class", "SubHeader")
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
        
        layout.addSpacing(10)
        
        # Instructions
        info = QLabel("Please contact our support team to activate your account. Provide your email address for faster verification.")
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #475569; line-height: 1.4;")
        layout.addWidget(info)
        
        layout.addSpacing(10)
        
        # Contact Cards
        from config.config import COMPANY_FACEBOOK, COMPANY_WECHAT, COMPANY_MESSAGING_PHONE
        
        contacts_layout = QVBoxLayout()
        contacts_layout.setSpacing(10)
        
        self.add_contact_card(contacts_layout, "Facebook Page", COMPANY_FACEBOOK, "📘")
        self.add_contact_card(contacts_layout, "WeChat ID", COMPANY_WECHAT, "💬")
        self.add_contact_card(contacts_layout, "Phone / Viber / Telegram", COMPANY_MESSAGING_PHONE, "📞")
        
        layout.addLayout(contacts_layout)
        
        layout.addStretch()
        
        # Back Button
        btn = QPushButton("Back to Login")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)
        btn.clicked.connect(self.back_to_login.emit)
        layout.addWidget(btn)

    def add_contact_card(self, parent_layout, label, value, icon):
        card = QFrame()
        card.setProperty("class", "ContactCard")
        cl = QHBoxLayout(card)
        cl.setContentsMargins(15, 12, 15, 12)
        
        ic = QLabel(icon)
        ic.setStyleSheet("font-size: 20px; margin-right: 10px;")
        cl.addWidget(ic)
        
        vl = QVBoxLayout()
        vl.setSpacing(2)
        l = QLabel(label)
        l.setProperty("class", "ContactLabel")
        v = QLabel(value)
        v.setProperty("class", "ContactValue")
        v.setTextInteractionFlags(Qt.TextSelectableByMouse)
        vl.addWidget(l)
        vl.addWidget(v)
        
        cl.addLayout(vl)
        cl.addStretch()
        
        parent_layout.addWidget(card)

class PermissionErrorView(QFrame):
    back_to_login = Signal()

    def __init__(self, title_text, msg_text, parent_dialog=None):
        super().__init__(parent_dialog)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        
        icon = QLabel("⚠️")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 48px;")
        self.layout.addWidget(icon)
        
        h = QLabel(title_text)
        h.setStyleSheet("font-size: 20px; font-weight: bold; color: #EF4444;")
        h.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(h)
        
        sh = QLabel(msg_text)
        sh.setStyleSheet("font-size: 14px; color: #64748B;")
        sh.setAlignment(Qt.AlignCenter)
        sh.setWordWrap(True)
        self.layout.addWidget(sh)
        
        btn = QPushButton("Back")
        btn.setStyleSheet("background: #0F172A; color: white; padding: 10px; border-radius: 8px;")
        btn.clicked.connect(self.back_to_login.emit)
        self.layout.addWidget(btn)

class OnlineLoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MSA Activation")
        self.setWindowModality(Qt.ApplicationModal)
        
        # Responsive Sizing for Classic UI
        screen_height = QApplication.primaryScreen().availableGeometry().height()
        target_height = min(750, screen_height - 60)
        self.resize(430, target_height)
        
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        
        self.license_service = LicenseService()
        self.fingerprint = self.license_service.get_machine_fingerprint()

        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area to handle overflow on small screens
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        
        self.stack = QStackedWidget()
        
        # --- Page 1: Login ---
        self.login_view = LoginView(settings_prefix="online_auth")
        self.login_view.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        self.login_view.username_label.setText("Email Address")
        self.login_view.username_input.setPlaceholderText("Enter Email Address")
        self.login_view.set_register_visible(True)
        self.login_view.login_attempt.connect(self.handle_login)
        self.login_view.register_requested.connect(lambda: self.stack.setCurrentIndex(1))

        # --- Page 2: Register ---
        self.register_view = RegisterView()
        self.register_view.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        self.register_view.email_input.setPlaceholderText("Enter Email Address")
        self.register_view.register_attempt.connect(self.handle_register)
        self.register_view.back_to_login.connect(lambda: self.stack.setCurrentIndex(0))
        
        # --- Page 3: Pending ---
        self.pending_view = PendingApprovalView()
        self.pending_view.back_to_login.connect(lambda: self.stack.setCurrentIndex(0))
        
        self.stack.addWidget(self.login_view)
        self.stack.addWidget(self.register_view)
        self.stack.addWidget(self.pending_view)
        
        self.scroll_area.setWidget(self.stack)
        self.main_layout.addWidget(self.scroll_area)

    def handle_login(self, email, password, remember=False):
        self.login_view.login_btn.setText("Authenticating...")
        self.login_view.login_btn.setEnabled(False)
        self.login_view.repaint()
        
        self.worker = AuthWorker(self.license_service.login_online, email, password, self.fingerprint)
        self.worker.finished.connect(self.on_login_finished)
        self.worker.start()

    def on_login_finished(self, result):
        self.login_view.reset_ui()
        
        is_valid = result.get('valid', False)
        msg = result.get('message', '')
        
        if is_valid or "subscription" in msg.lower() or "expired" in msg.lower():
            from PySide6.QtCore import QSettings
            from config.config import SETTINGS_ORGANIZATION, SETTINGS_APPLICATION
            settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
            remember = self.login_view.remember_me_cb.isChecked()
            email = self.login_view.username_input.text()
            
            if remember:
                settings.setValue("online_auth/remember_me", True)
                settings.setValue("online_auth/remember_username", email)
            else:
                settings.setValue("online_auth/remember_me", False)
                settings.remove("online_auth/remember_username")

        if is_valid:
            QMessageBox.information(self, "Welcome", "Device Activated Successfully!")
            self.accept()
        else:
            if "subscription" in msg.lower():
                self.stack.addWidget(PermissionErrorView("Authentication Issue", msg, self))
                self.stack.setCurrentIndex(self.stack.count() - 1)
            else:
                QMessageBox.warning(self, "Activation Failed", msg)

    def handle_register(self, username, email, password, phone, city, country):
        self.setCursor(Qt.WaitCursor)
        self.register_view.register_btn.setEnabled(False)
        self.register_view.register_btn.setText("Registering...")
        self.repaint()
        
        self.worker = AuthWorker(
            self.license_service.register_online, 
            email, password, self.fingerprint, 
            name=username, phone=phone, city=city, country=country
        )
        self.worker.finished.connect(self.on_register_finished)
        self.worker.start()

    def on_register_finished(self, result):
        self.setCursor(Qt.ArrowCursor)
        self.register_view.register_btn.setEnabled(True)
        self.register_view.register_btn.setText("Create Account")
        
        if result.get('success', False):
            self.stack.setCurrentIndex(2)
        else:
            QMessageBox.warning(self, "Registration Failed", result.get('message', 'Error'))
            
    def apply_styles(self):
        pass
