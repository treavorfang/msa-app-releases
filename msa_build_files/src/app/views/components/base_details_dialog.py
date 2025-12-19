# src/app/views/components/base_details_dialog.py
"""
Base class for details dialogs with tabbed interface.
Provides common functionality for customer, technician, supplier, and part details.
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QTabWidget, QWidget)
from PySide6.QtCore import Qt
from typing import Optional


class BaseDetailsDialog(QDialog):
    """Base class for details dialogs with tabbed interface"""
    
    def __init__(self, title: str, icon: str = "📄", parent=None):
        super().__init__(parent)
        self.dialog_title = title
        self.dialog_icon = icon
        self._setup_base_ui()
    
    def _setup_base_ui(self):
        """Setup the base UI structure"""
        self.setWindowTitle(self.dialog_title)
        self.setMinimumSize(600, 400)
        
        self.main_layout = QVBoxLayout(self)
        
        # Header will be added by subclass
        self.header_layout = QHBoxLayout()
        self.main_layout.addLayout(self.header_layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Button layout
        self.button_layout = QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)
        
        # Add default close button
        self._add_default_buttons()
    
    def _add_default_buttons(self):
        """Add default close button"""
        self.button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        self.button_layout.addWidget(close_btn)
    
    def add_header(self, title: str, status: Optional[str] = None, 
                   status_color: Optional[str] = None):
        """Add header with title and optional status badge"""
        title_label = QLabel(f"{self.dialog_icon} {title}")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.header_layout.addWidget(title_label)
        
        if status and status_color:
            status_badge = self._create_status_badge(status, status_color)
            self.header_layout.addWidget(status_badge)
        
        self.header_layout.addStretch()
    
    def _create_status_badge(self, text: str, color: str) -> QLabel:
        """Create a status badge"""
        badge = QLabel(f" {text} ")
        badge.setStyleSheet(f"""
            background-color: {color}; 
            color: white; 
            border-radius: 4px; 
            padding: 4px; 
            font-weight: bold;
        """)
        return badge
    
    def add_tab(self, widget: QWidget, title: str):
        """Add a tab to the dialog"""
        self.tabs.addTab(widget, title)
    
    def add_action_button(self, text: str, callback, position: int = 0):
        """Add an action button before the close button"""
        button = QPushButton(text)
        button.clicked.connect(callback)
        self.button_layout.insertWidget(position, button)
        return button


class StatusBadge(QLabel):
    """Reusable status badge component"""
    
    def __init__(self, text: str, color: str, parent=None):
        super().__init__(f" {text} ", parent)
        self.setStyleSheet(f"""
            background-color: {color}; 
            color: white; 
            border-radius: 4px; 
            padding: 4px; 
            font-weight: bold;
        """)
