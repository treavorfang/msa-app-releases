# src/app/views/setting/tabs/general.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QGroupBox, 
                              QPushButton, QLabel, QComboBox, QSpinBox, 
                              QCheckBox, QHBoxLayout, QFrame)
from PySide6.QtCore import Qt
from utils.language_manager import language_manager
from utils.currency_formatter import currency_formatter

import os
import configparser

class GeneralTab(QWidget):
    def __init__(self, container, user):
        super().__init__()
        self.container = container
        self.user = user
        self.lm = language_manager
        
        # Load current language from settings to initialize LanguageManager
        settings = self.container.settings_service.get_user_settings(self.user.id)
        current_lang = settings.get('language', 'en')  # Default to 'en' code
        self.lm.load_language(current_lang)
        
        self._setup_ui()
        self._load_settings()
        self._update_theme_display()
        
    def _get_available_currencies(self):
        """Scan language files to find supported currencies"""
        # Dictionary to deduplicate by code
        # Initialize with defaults (English names preferred)
        currencies_map = {
            "USD": "US Dollar",
            "MMK": "Myanmar Kyat"
        }
        
        try:
            languages_dir = self.lm.languages_dir
            if os.path.exists(languages_dir):
                for filename in os.listdir(languages_dir):
                    if filename.endswith(".ini"):
                        try:
                            parser = configparser.ConfigParser()
                            parser.read(os.path.join(languages_dir, filename), encoding='utf-8')
                            if parser.has_section("Currency"):
                                code = parser.get("Currency", "code", fallback="").upper()
                                name = parser.get("Currency", "name", fallback="")
                                
                                # Add only if code not present (preserves Defaults/English names)
                                if code and name and code not in currencies_map:
                                    currencies_map[code] = name
                        except Exception:
                            continue
        except Exception:
            pass
            
        return sorted([f"{code} - {name}" for code, name in currencies_map.items()])

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel(self.lm.get("General.settings_title", "Settings"))
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Main Content Area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Left Column - App & Interface
        left_column = QVBoxLayout()
        left_column.setSpacing(20)
        
        # Application Settings Group
        app_group = self._create_group_box(self.lm.get("General.app_settings", "Application Settings"))
        app_layout = QFormLayout(app_group)
        app_layout.setSpacing(15)

        # Language selection
        self.language_combo = QComboBox()
        # Populate with available languages (display name as text, code as data)
        for lang in self.lm.get_available_languages():
            self.language_combo.addItem(lang['name'], lang['code'])
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        app_layout.addRow(self.lm.get("Settings.language", "Language:"), self.language_combo)

        # Date format
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems([
            "YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY", "Month DD, YYYY"
        ])
        self.date_format_combo.currentTextChanged.connect(lambda t: self._on_generic_setting_changed('date_format', t))
        app_layout.addRow(self.lm.get("Settings.date_format", "Date Format:"), self.date_format_combo)

        # Print Format
        self.print_format_combo = QComboBox()
        self.print_format_combo.addItems(["Standard A5", "Thermal 80mm", "Thermal 58mm"])
        self.print_format_combo.currentTextChanged.connect(lambda t: self._on_generic_setting_changed('print_format', t))
        app_layout.addRow(self.lm.get("Settings.print_format", "Print Format:"), self.print_format_combo)

        # Auto Print - Side by Side
        auto_print_layout = QHBoxLayout()
        self.auto_print_ticket = QCheckBox(self.lm.get("Settings.auto_print_ticket", "Auto-print Tickets"))
        self.auto_print_ticket.toggled.connect(lambda c: self._on_generic_setting_changed('auto_print_ticket', c))
        auto_print_layout.addWidget(self.auto_print_ticket)
        
        self.auto_print_invoice = QCheckBox(self.lm.get("Settings.auto_print_invoice", "Auto-print Invoices"))
        self.auto_print_invoice.toggled.connect(lambda c: self._on_generic_setting_changed('auto_print_invoice', c))
        auto_print_layout.addWidget(self.auto_print_invoice)
        
        app_layout.addRow("", auto_print_layout)

        # Time format
        self.time_format_combo = QComboBox()
        self.time_format_combo.addItems(["12-hour", "24-hour"])
        self.time_format_combo.currentTextChanged.connect(lambda t: self._on_generic_setting_changed('time_format', t))
        app_layout.addRow(self.lm.get("Settings.time_format", "Time Format:"), self.time_format_combo)

        # Currency selection
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(self._get_available_currencies())
        self.currency_combo.currentTextChanged.connect(self._on_currency_changed)
        app_layout.addRow(self.lm.get("Settings.currency", "Currency:"), self.currency_combo)
        
        # Currency preview
        self.currency_preview = QLabel("$1,234.56")
        self.currency_preview.setStyleSheet("color: #10B981; font-weight: bold; font-size: 14px;")
        app_layout.addRow(self.lm.get("Settings.currency_preview", "Preview:"), self.currency_preview)
        


        left_column.addWidget(app_group)
        
        # Interface Settings Group
        interface_group = self._create_group_box(self.lm.get("General.interface_settings", "Interface Settings"))
        interface_layout = QFormLayout(interface_group)
        interface_layout.setSpacing(15)

        # Startup behavior
        self.startup_combo = QComboBox()
        self.startup_combo.addItems([
            "Show Dashboard", 
            "Show Last Active Tab", 
            "Show Tickets", 
            "Show Jobs"
        ])
        self.startup_combo.currentTextChanged.connect(lambda t: self._on_generic_setting_changed('startup_view', t))
        interface_layout.addRow(self.lm.get("Settings.startup_view", "Startup View:"), self.startup_combo)
        
        # Session timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 240)
        self.timeout_spin.setSuffix(" minutes")
        self.timeout_spin.valueChanged.connect(lambda v: self._on_generic_setting_changed('session_timeout', v))
        interface_layout.addRow(self.lm.get("Settings.session_timeout", "Session Timeout:"), self.timeout_spin)

        left_column.addWidget(interface_group)
        content_layout.addLayout(left_column)

        # Right Column - Appearance & Notifications
        right_column = QVBoxLayout()
        right_column.setSpacing(20)

        # Theme Settings Group
        theme_group = self._create_group_box(self.lm.get("Settings.theme", "Appearance"))
        theme_layout = QFormLayout(theme_group)
        theme_layout.setSpacing(15)

        self.theme_combo = QComboBox()
        if self.container.theme_controller:
            for theme_id, theme_data in self.container.theme_controller.available_themes.items():
                self.theme_combo.addItem(theme_data.get("name", theme_id.capitalize()), theme_id)
        theme_layout.addRow(self.lm.get("Settings.theme", "Theme:"), self.theme_combo)

        self.theme_toggle = QPushButton(self.lm.get("Themes.toggle_button", "Toggle Light/Dark Theme"))
        theme_layout.addRow("Quick Toggle:", self.theme_toggle)

        # Font settings
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems(["Small", "Medium", "Large", "Extra Large"])
        self.font_size_combo.currentTextChanged.connect(lambda t: self._on_generic_setting_changed('font_size', t))
        theme_layout.addRow(self.lm.get("Settings.font_size", "Font Size:"), self.font_size_combo)
        
        right_column.addWidget(theme_group)

        # Notifications Group
        notify_group = self._create_group_box(self.lm.get("Settings.notifications", "Notifications"))
        notify_layout = QVBoxLayout(notify_group)
        
        self.notify_email = QCheckBox(self.lm.get("Notifications.email", "Email Notifications"))
        self.notify_email.toggled.connect(lambda c: self._on_generic_setting_changed('notify_email', c))
        
        self.notify_desktop = QCheckBox(self.lm.get("Notifications.desktop", "Desktop Notifications"))
        self.notify_desktop.toggled.connect(lambda c: self._on_generic_setting_changed('notify_desktop', c))
        
        self.notify_sound = QCheckBox(self.lm.get("Notifications.sound", "Sound Alerts"))
        self.notify_sound.toggled.connect(lambda c: self._on_generic_setting_changed('notify_sound', c))
        
        notify_layout.addWidget(self.notify_email)
        notify_layout.addWidget(self.notify_desktop)
        notify_layout.addWidget(self.notify_sound)
        
        right_column.addWidget(notify_group)
        content_layout.addLayout(right_column)
        
        layout.addLayout(content_layout)
        layout.addStretch()
        
        # Connect signals
        self.theme_toggle.clicked.connect(self._on_theme_toggle)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)

    def _create_group_box(self, title):
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 24px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        return group

    def _load_settings(self):
        """Load saved settings from configuration"""
        settings = self.container.settings_service.get_user_settings(self.user.id)
        
        # Block signals to prevent auto-save loops during loading
        widgets = [
            self.language_combo, self.date_format_combo, self.time_format_combo,
            self.currency_combo, self.font_size_combo, self.startup_combo,
            self.timeout_spin, self.notify_email, self.notify_desktop, self.notify_sound,
            self.print_format_combo, self.auto_print_ticket, self.auto_print_invoice
        ]
        
        for w in widgets:
            w.blockSignals(True)
            
        try:
            # Find and set current language by code
            current_lang_code = settings.get('language', 'en')
            lang_index = self.language_combo.findData(current_lang_code)
            if lang_index >= 0:
                self.language_combo.setCurrentIndex(lang_index)
            
            self.date_format_combo.setCurrentText(settings.get('date_format', 'MM/DD/YYYY'))
            self.print_format_combo.setCurrentText(settings.get('print_format', 'Standard A5'))
            self.auto_print_ticket.setChecked(settings.get('auto_print_ticket', True))
            self.auto_print_invoice.setChecked(settings.get('auto_print_invoice', True))
            self.time_format_combo.setCurrentText(settings.get('time_format', '12-hour'))
            self.currency_combo.setCurrentText(settings.get('currency', 'USD - US Dollar'))
            self.font_size_combo.setCurrentText(settings.get('font_size', 'Medium'))
            self.startup_combo.setCurrentText(settings.get('startup_view', 'Show Dashboard'))
            self.timeout_spin.setValue(settings.get('session_timeout', 30))
            
            self.notify_email.setChecked(settings.get('notify_email', True))
            self.notify_desktop.setChecked(settings.get('notify_desktop', True))
            self.notify_sound.setChecked(settings.get('notify_sound', False))
        finally:
            for w in widgets:
                w.blockSignals(False)

    def _on_generic_setting_changed(self, key, value):
        """Generic handler for auto-saving settings values"""
        settings = self.container.settings_service.get_user_settings(self.user.id)
        settings[key] = value
        self.container.settings_service.save_user_settings(self.user.id, settings)
        print(f"Auto-saved setting: {key} = {value}")

    def _apply_settings(self, settings):
        """Apply settings that take immediate effect"""
        pass
        
    def _on_theme_toggle(self):
        """Handle theme toggle and update display"""
        if self.container.theme_controller:
            self.container.theme_controller.toggle_theme()
            self._update_theme_display()

    def _on_theme_changed(self):
        """Handle theme selection from combo box"""
        if self.container.theme_controller:
            theme_id = self.theme_combo.currentData()
            self.container.theme_controller.load_theme(theme_id)
            self._update_theme_display()

    def _update_theme_display(self):
        """Update the theme label with current theme"""
        if self.container.theme_controller:
            current_theme = self.container.theme_controller.current_theme
            # Update combo box selection
            index = self.theme_combo.findData(current_theme)
            if index >= 0:
                self.theme_combo.blockSignals(True)
                self.theme_combo.setCurrentIndex(index)
                self.theme_combo.blockSignals(False)

    def update_theme_label(self, theme_name=None):
        """Public method to update theme display, compatible with SettingsTab call"""
        self._update_theme_display()
    
    def _on_language_changed(self, index):
        """Handle language selection change and prompt for restart"""
        from PySide6.QtWidgets import QMessageBox, QApplication
        import sys

        if index < 0:
            return
        
        # Get the language code from the combobox data
        new_language_code = self.language_combo.currentData()
        
        if not new_language_code or new_language_code == self.lm.current_language:
            return
        
        # Load the new language
        self.lm.load_language(new_language_code)
        
        # Reload currency formatter with new language settings
        currency_formatter.reload()
        
        # Update currency preview with new formatting
        self.currency_preview.setText(currency_formatter.format(1234.56))
        
        # Save the language preference (save the code)
        settings = self.container.settings_service.get_user_settings(self.user.id)
        settings['language'] = new_language_code
        self.container.settings_service.save_user_settings(self.user.id, settings)
        
        # Also save to global QSettings for Login Screen
        from PySide6.QtCore import QSettings
        from config.config_manager import SETTINGS_ORGANIZATION, SETTINGS_APPLICATION
        q_settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
        q_settings.setValue("system/language", new_language_code)
        
        print(f"✅ Language changed to: {self.lm.get_language_name(new_language_code)}")
        
        # Prompt for restart
        reply = QMessageBox.question(
            self, 
            self.lm.get("Settings.restart_required", "Restart Required"),
            self.lm.get("Settings.restart_confirm", "Language change requires a restart to apply completely.\nDo you want to restart now?"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            # Restart the application
            if getattr(sys, 'frozen', False):
                # If packaged (PyInstaller), executable is the app itself
                os.execl(sys.executable, sys.executable, *sys.argv[1:])
            else:
                # If dev (Python), executable is python interpreter
                os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            # Inform user it will apply next time
            pass
    
    def _on_currency_changed(self, currency_text):
        """Handle currency selection change and update preview"""
        # Extract currency code from selection (e.g., "USD - US Dollar" -> "USD")
        currency_code = currency_text.split(" - ")[0]
        
        # Save the currency preference immediately
        settings = self.container.settings_service.get_user_settings(self.user.id)
        settings['currency'] = currency_text
        self.container.settings_service.save_user_settings(self.user.id, settings)
        
        # Update currency formatter overrides
        currency_formatter.set_currency_overrides(currency_code)
        
        
        # Update preview directly
        self.currency_preview.setText(currency_formatter.format(1234.56))