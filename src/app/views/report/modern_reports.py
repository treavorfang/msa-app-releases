# src/app/views/report/reports.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QComboBox, QDateEdit, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QLabel, QGroupBox, QTabWidget, QFrame,
                               QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QDate, QPropertyAnimation, QEasingCurve, QRect, Property
from PySide6.QtGui import QColor, QPalette
from datetime import datetime, timedelta

class ModernMetricCard(QFrame):
    """Modern metric card with theme support and animations"""
    
    def __init__(self, title, value, color, icon, parent=None):
        super().__init__(parent)
        self.color = color
        self._setup_ui(title, value, icon)
        self._setup_animation()
    
    def _setup_ui(self, title, value, icon):
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(140)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        
        # Icon container with colored background
        icon_container = QFrame()
        icon_container.setFixedSize(48, 48)
        icon_container.setStyleSheet(f"""
            QFrame {{
                background-color: {self.color};
                border-radius: 24px;
            }}
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px; background: transparent;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon_label)
        
        header_layout.addWidget(icon_container)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 500;
            opacity: 0.7;
        """)
        layout.addWidget(title_label)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            font-size: 32px;
            font-weight: bold;
            color: {self.color};
        """)
        self.value_label.setObjectName("value_label")
        layout.addWidget(self.value_label)
        
        layout.addStretch()
    
    def _setup_animation(self):
        """Setup hover animation"""
        self.setProperty("hovered", False)
    
    def enterEvent(self, event):
        """Animate on hover"""
        self.setProperty("hovered", True)
        self.style().unpolish(self)
        self.style().polish(self)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Animate on leave"""
        self.setProperty("hovered", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().leaveEvent(event)

class ReportsTab(QWidget):
    def __init__(self, container):
        super().__init__()
