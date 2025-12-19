# src/app/views/dialogs/forgot_password_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from config.config import ICON_PATHS

class ForgotPasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reset Password")
        self.setFixedSize(400, 300)
        if 'logo' in ICON_PATHS:
            self.setWindowIcon(QIcon(ICON_PATHS['logo']))
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; color: #ffffff; }
            QLabel { color: #e0e0e0; font-size: 13px; }
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header = QLabel("Reset Password")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #444;")
        layout.addWidget(line)
        
        # Info Text
        info = QLabel(
            "For security reasons, locally stored passwords cannot be recovered via email.\n\n"
            "<b>Are you a Staff member?</b>\n"
            "Please contact your Administrator (Manager). They can reset your password from the Admin Dashboard.\n\n"
            "<b>Are you the Administrator?</b>\n"
            "Please contact <b>Studio Tai Support</b> with your License Key for an emergency reset token."
        )
        info.setWordWrap(True)
        info.setStyleSheet("line-height: 1.4;")
        layout.addWidget(info)
        
        layout.addStretch()
        
        # Close Button
        close_btn = QPushButton("Understood")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
