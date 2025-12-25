from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
import qrcode
import io
from PIL import Image

from utils.language_manager import language_manager
from utils.mobile_utils import generate_daily_pin, get_pairing_url
from config.flags import get_config

class MobilePairingDialog(QDialog):
    """Dialog that displays a QR code for mobile pairing."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lm = language_manager
        self.config = get_config()
        self._setup_ui()
        
    def _setup_ui(self):
        self.setWindowTitle(self.lm.get("Dashboard.mobile_pairing", "Mobile Pairing"))
        self.setFixedSize(400, 580)
        self.setStyleSheet("background-color: #1F2937; color: white;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel(self.lm.get("Dashboard.pair_device", "Pair Your Device"))
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #F59E0B;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Instructions
        desc = QLabel(self.lm.get("Dashboard.pair_desc", "Scan this code with your phone camera to connect to the workbench instantly."))
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #9CA3AF; font-size: 14px;")
        layout.addWidget(desc)
        
        # QR Code Frame
        self.qr_label = QLabel()
        self.qr_label.setFixedSize(250, 250)
        self.qr_label.setStyleSheet("background-color: white; border-radius: 12px; padding: 10px;")
        self.qr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.qr_label, 0, Qt.AlignCenter)
        
        # Today's PIN Label
        pin_container = QFrame()
        pin_container.setStyleSheet("background-color: #374151; border-radius: 8px; padding: 5px 20px;")
        pin_layout = QHBoxLayout(pin_container)
        
        pin_text = QLabel(self.lm.get("Dashboard.todays_pin", "Today's PIN"))
        pin_text.setStyleSheet("font-size: 11px; color: #9CA3AF; text-transform: uppercase; font-weight: bold;")
        pin_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        pin_layout.addWidget(pin_text)
        
        pin_layout.addStretch()
        
        self.pin_val = QLabel(generate_daily_pin())
        self.pin_val.setStyleSheet("font-size: 24px; font-weight: 800; color: #F59E0B; letter-spacing: 3px;")
        self.pin_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pin_layout.addWidget(self.pin_val)
        
        layout.addWidget(pin_container)
        
        # URL Display for troubleshooting
        self.url_label = QLabel()
        self.url_label.setStyleSheet("color: #6B7280; font-size: 11px;")
        self.url_label.setAlignment(Qt.AlignCenter)
        self.url_label.setWordWrap(True)
        layout.addWidget(self.url_label)
        
        # Close Button
        close_btn = QPushButton(self.lm.get("Common.close", "Close"))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4B5563;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #6B7280; }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self._generate_qr()
        
    def _generate_qr(self):
        """Generate QR code image from pairing URL."""
        port = self.config.get('mobile_server_port', 8000)
        url = get_pairing_url(port)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Update troubleshooting label
        self.url_label.setText(f"Connection URL: {url}")
        
        # Convert PIL image to QPixmap
        byte_array = io.BytesIO()
        img.save(byte_array, format='PNG')
        qimage = QImage.fromData(byte_array.getvalue())
        pixmap = QPixmap.fromImage(qimage)
        
        self.qr_label.setPixmap(pixmap.scaled(230, 230, Qt.KeepAspectRatio, Qt.SmoothTransformation))
