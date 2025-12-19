"""
Main window for License Generator - Final Compact Design with Tabs
"""
import os
from datetime import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel,  QTabWidget, QApplication, QPushButton)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPixmap, QFont

from core import LOGO_PATH
from core.firebase_manager import OnlineManager
from .styles import MAIN_WINDOW_STYLE, TAB_STYLE
from .customer_dashboard import HistoryView 

class LicenseGeneratorWindow(QMainWindow):
    """Main application window - Compact Professional Design"""
    
    def __init__(self):
        super().__init__()
        self.manager = OnlineManager()
        
        self.setWindowTitle("MSA Admin Dashboard")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup compact professional UI with Tabs"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header (Common)
        layout.addLayout(self._create_header())
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)
        
        # Tab 1: Customer Dashboard (HistoryView -> Online)
        self.dashboard_tab = HistoryView()
        self.tabs.addTab(self.dashboard_tab, "👥 Customer Dashboard")
        
        # Tab 2: Invoices
        from .invoices_view import InvoicesView
        self.invoices_tab = InvoicesView()
        self.tabs.addTab(self.invoices_tab, "💰 Financial Records")
        
        # Tab 3: Audit Logs
        from .audit_view import AuditLogView
        self.audit_tab = AuditLogView()
        self.tabs.addTab(self.audit_tab, "🛡️ System Audit Logs")
        
        layout.addWidget(self.tabs)
        
        self.statusBar().showMessage("Ready")
    
    def _create_header(self):
        """Create compact header"""
        header_font = QFont()
        header_font.setPointSize(11)
        header_font.setBold(True)
        
        layout = QHBoxLayout()
        layout.setSpacing(5)
        
        # Logo
        if os.path.exists(LOGO_PATH):
            logo_label = QLabel()
            pixmap = QPixmap(LOGO_PATH)
            scaled_pixmap = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            layout.addWidget(logo_label)
        
        # Title
        title = QLabel("MSA License Monitor System")
        title.setFont(header_font)
        title.setStyleSheet("color: #3b82f6; font-size: 18px;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Date
        today = QLabel(QDate.currentDate().toString("MMM d, yyyy"))
        today.setFont(header_font)
        layout.addWidget(QLabel("Date:"))
        layout.addWidget(today)
        
        # Spacer
        layout.addSpacing(15)
        
        # About Button
        from .about_dialog import AboutDialog
        btn_about = QPushButton("ℹ️ About")
        btn_about.setCursor(Qt.PointingHandCursor)
        btn_about.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 4px 10px;
                color: #d1d5db;
            }
            QPushButton:hover {
                background-color: #374151;
                color: white;
            }
        """)
        btn_about.clicked.connect(lambda: AboutDialog(self).exec())
        layout.addWidget(btn_about)
        
        return layout
