# src/app/controllers/theme_controller.py
from PySide6.QtCore import QFile, QTextStream, QSettings
from PySide6.QtWidgets import QApplication
from config.config_manager import SETTINGS_ORGANIZATION, SETTINGS_APPLICATION, DEFAULT_THEME, THEME_SETTING_KEY, THEMES

class ThemeController:
    def __init__(self, app):
        self.app = app
        self.settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
        self.available_themes = THEMES  # Initialize available_themes FIRST
        self.current_theme = self._load_saved_theme()  # Then load saved theme
        
    def _load_saved_theme(self):
        """Load the saved theme from QSettings or use default"""
        saved_theme = self.settings.value(THEME_SETTING_KEY, DEFAULT_THEME)
        if saved_theme in self.available_themes:
            return saved_theme
        return DEFAULT_THEME
        
    def _save_theme(self, theme_name):
        """Save the theme preference to QSettings"""
        self.settings.setValue(THEME_SETTING_KEY, theme_name)
        self.settings.sync()  # Ensure it's written to disk
        
    def load_theme(self, theme_name):
        """Load a theme using the path from settings"""
        if theme_name not in self.available_themes:
            print(f"Theme {theme_name} not found in available themes")
            return
            
        theme_path = self.available_themes[theme_name]["path"]
        
        file = QFile(theme_path)
        if file.open(QFile.ReadOnly | QFile.Text):
            stream = QTextStream(file)
            self.app.setStyleSheet(stream.readAll())
            file.close()
            self.current_theme = theme_name
            self._save_theme(theme_name)  # Save the theme preference
        else:
            print(f"Failed to load theme: {theme_path}")
            
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        if self.current_theme == 'dark':
            self.load_theme('light')
        else:
            self.load_theme('dark')
            
    def get_available_themes(self):
        """Return list of available theme names"""
        return list(self.available_themes.keys())