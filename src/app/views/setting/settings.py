
# src/app/views/settings/settings.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget
from views.setting.tabs.general import GeneralTab
from views.setting.tabs.data import DataTab
from utils.language_manager import language_manager


class SettingsTab(QWidget):
    def __init__(self, container, user):
        super().__init__()
        self.container = container
        self.user = user
        self.lm = language_manager
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab widget for different setting categories
        self.tabs = QTabWidget()
        
        # Create tab instances
        self.general_tab = GeneralTab(self.container, self.user)
        self.data_tab = DataTab(self.container, self.user)
        
        # Add tabs to tab widget
        self.tabs.addTab(self.general_tab, self.lm.get("Settings.general", "General"))
        self.tabs.addTab(self.data_tab, self.lm.get("Settings.data", "Data & Backup"))
        
        layout.addWidget(self.tabs)
    
    def _is_admin(self):
        """Check if current user is admin using RoleService"""
        return self.container.role_service.user_has_role(self.user, 'admin')

    def _connect_signals(self):
        """Connect signals for theme changes"""
        # Connect theme toggle button
        if self.container.theme_controller:
            # Update theme label with current theme on initialization
            current_theme = self.container.theme_controller.current_theme
            self.general_tab.update_theme_label(current_theme)