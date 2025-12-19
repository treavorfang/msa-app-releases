"""SettingsService - User Preferences Management.

This service manages user-specific application settings (like theme, language)
persisted in JSON files within the user's home directory.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class SettingsService:
    """Service class for User Settings operations."""
    
    def __init__(self, app_data_dir: Optional[str] = None):
        """Initialize SettingsService.
        
        Args:
            app_data_dir: Custom directory for app data (defaults to ~/.msa_app)
        """
        self.app_data_dir = app_data_dir or str(Path.home() / ".msa_app")
        self.settings_dir = os.path.join(self.app_data_dir, "settings")
        os.makedirs(self.settings_dir, exist_ok=True)
        
        # Default settings configuration
        self.default_settings = {
            'language': 'English',
            'date_format': 'MM/DD/YYYY',
            'time_format': '12-hour',
            'font_size': 'Medium',
            'startup_view': 'Show Dashboard',
            'session_timeout': 30,
            'notify_email': True,
            'notify_desktop': True,
            'notify_sound': False,
            'theme': 'light'
        }

    def _get_settings_path(self, user_id: int) -> str:
        """Get the file path for a user's settings file."""
        return os.path.join(self.settings_dir, f"user_{user_id}.json")

    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user settings, merging with defaults if custom settings exist."""
        settings_path = self._get_settings_path(user_id)
        
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r') as f:
                    user_settings = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return {**self.default_settings, **user_settings}
            except (json.JSONDecodeError, IOError):
                # Fallback on error
                return self.default_settings.copy()
        
        return self.default_settings.copy()

    def save_user_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """Save user settings to their JSON file."""
        try:
            settings_path = self._get_settings_path(user_id)
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except IOError:
            return False

    def reset_user_settings(self, user_id: int) -> bool:
        """Reset user settings by deleting the custom settings file."""
        settings_path = self._get_settings_path(user_id)
        if os.path.exists(settings_path):
            try:
                os.remove(settings_path)
                return True
            except IOError:
                return False
        return True