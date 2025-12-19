
import sys
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton, 
                               QVBoxLayout, QHBoxLayout, QFrame, QCheckBox, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QPoint, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QFont, QLinearGradient, QGradient, QPainter, QBrush, QPen

class ModernLoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MSA Modern Login")
        self.resize(1000, 700)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.old_pos = None
        self.init_ui()

    def init_ui(self):
        # 1. Main Layout
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10) # Margin for shadow

        # 2. Background Container (Dark Blurred Theme)
        self.bg_frame = QFrame()
        self.bg_frame.setObjectName("MainFrame")
        self.bg_frame.setStyleSheet("""
            QFrame#MainFrame {
                background: qradialgradient(cx:0.5, cy:0.5, radius: 1.0, fx:0.5, fy:0.5, stop:0 #1F2937, stop:1 #0F172A); /* Radial dark blue/black */
                border-radius: 12px;
                border: 1px solid #334155;
            }
        """)
        
        # Window Shadow
        win_shadow = QGraphicsDropShadowEffect(self)
        win_shadow.setBlurRadius(20)
        win_shadow.setColor(QColor(0, 0, 0, 180))
        win_shadow.setOffset(0, 0)
        self.bg_frame.setGraphicsEffect(win_shadow)

        root_layout.addWidget(self.bg_frame)

        # 3. Inner Layout to center the card
        bg_layout = QVBoxLayout(self.bg_frame)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Top Bar (Close Button) ---
        top_bar = QWidget()
        top_bar.setFixedHeight(40)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 10, 0)
        top_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton { color: #94A3B8; background: transparent; border: none; font-size: 14px; }
            QPushButton:hover { color: white; background-color: #EF4444; border-radius: 15px; }
        """)
        close_btn.clicked.connect(self.close)
        top_layout.addWidget(close_btn)
        
        bg_layout.addWidget(top_bar)
        bg_layout.addStretch()

        # --- CENTER CARD ---
        center_row = QHBoxLayout()
        center_row.addStretch()
        
        self.card = QFrame()
        self.card.setFixedSize(400, 500)
        self.card.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.7); /* Semi-transparent Slate 800 */
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        # Card Shadow (Glow)
        card_shadow = QGraphicsDropShadowEffect(self)
        card_shadow.setBlurRadius(40)
        card_shadow.setColor(QColor(0, 0, 0, 120))
        card_shadow.setOffset(0, 10)
        self.card.setGraphicsEffect(card_shadow)

        # Card Content
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)

        # Logo / Title
        logo = QLabel("MSA")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("""
            font-size: 48px; 
            font-weight: bold; 
            color: #60A5FA; /* Blue 400 */
            background: transparent;
            font-family: 'Arial';
        """)
        
        # Logo Glow Effect
        logo_glow = QGraphicsDropShadowEffect(self)
        logo_glow.setBlurRadius(20)
        logo_glow.setColor(QColor(96, 165, 250, 150)) # Blue glow
        logo_glow.setOffset(0, 0)
        logo.setGraphicsEffect(logo_glow)

        subtitle = QLabel("Mobile Service Accounting")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 14px; background: transparent; margin-bottom: 10px;")

        card_layout.addWidget(logo)
        card_layout.addWidget(subtitle)

        # Inputs
        user_group = QVBoxLayout()
        user_group.setSpacing(5)
        user_label = QLabel("Email")
        user_label.setStyleSheet("color: #CBD5E1; font-size: 12px; font-weight: bold; background: transparent;")
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Enter your email address")
        self.user_input.setFixedHeight(45)
        self.style_input(self.user_input)
        
        user_group.addWidget(user_label)
        user_group.addWidget(self.user_input)

        pass_group = QVBoxLayout()
        pass_group.setSpacing(5)
        pass_label = QLabel("Password")
        pass_label.setStyleSheet("color: #CBD5E1; font-size: 12px; font-weight: bold; background: transparent;")
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Enter password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setFixedHeight(45)
        self.style_input(self.pass_input)

        pass_group.addWidget(pass_label)
        pass_group.addWidget(self.pass_input)
        
        card_layout.addLayout(user_group)
        card_layout.addLayout(pass_group)

        # Options
        opts_layout = QHBoxLayout()
        self.remember = QCheckBox("Remember Me")
        self.remember.setCursor(Qt.PointingHandCursor)
        self.remember.setStyleSheet("""
            QCheckBox { color: #94A3B8; background: transparent; font-size: 12px; }
            QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px; border: 1px solid #475569; background: #0F172A; }
            QCheckBox::indicator:checked { background-color: #3B82F6; border-color: #3B82F6; }
        """)
        
        forgot = QLabel("Forgot password")
        forgot.setCursor(Qt.PointingHandCursor)
        forgot.setStyleSheet("color: #3B82F6; background: transparent; font-size: 12px; font-weight: bold;")
        
        opts_layout.addWidget(self.remember)
        opts_layout.addStretch()
        opts_layout.addWidget(forgot)
        
        card_layout.addLayout(opts_layout)
        card_layout.addSpacing(10)

        # Login Button
        btn = QPushButton("Login")
        btn.setFixedHeight(45)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #2563EB);
                color: white;
                font-size: 15px;
                font-weight: bold;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #60A5FA, stop:1 #3B82F6);
            }
        """)
        # Button Glow
        btn_glow = QGraphicsDropShadowEffect(self)
        btn_glow.setBlurRadius(15)
        btn_glow.setColor(QColor(37, 99, 235, 120))
        btn_glow.setOffset(0, 4)
        btn.setGraphicsEffect(btn_glow)
        
        card_layout.addWidget(btn)
        card_layout.addStretch()

        center_row.addWidget(self.card)
        center_row.addStretch()
        
        bg_layout.addLayout(center_row)
        bg_layout.addStretch()

    def style_input(self, widget):
        widget.setStyleSheet("""
            QLineEdit {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px solid #334155;
                border-radius: 8px;
                color: white;
                padding-left: 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
                background-color: rgba(15, 23, 42, 0.9);
            }
            QLineEdit::placeholder {
                color: #475569;
            }
        """)
    
    # --- Frameless Dragging ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Optional: Set a system-wide font if you have it, e.g., Inter
    font = QFont("Inter")
    font.setStyleHint(QFont.SansSerif)
    app.setFont(font)

    window = ModernLoginWindow()
    window.show()
    sys.exit(app.exec())
