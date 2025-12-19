# src/app/config/config_manager.py
from .config_loader import load_brands_config, load_phone_errors
from .config import (
    DATABASE_PATH, ICON_PATHS, PASSWORD_HASH_METHOD, PASSWORD_SALT_LENGTH, SESSION_TIMEOUT,
    APP_NAME, APP_SHORT_NAME, APP_VERSION, COMPANY_NAME, COMPANY_ADDRESS, COMPANY_PHONE,
    THEMES, DEFAULT_THEME, SETTINGS_ORGANIZATION, SETTINGS_APPLICATION, THEME_SETTING_KEY
)

class ConfigManager:
    """Centralized configuration manager"""
    
    def __init__(self):
        self._brands_config = None
        self._phone_errors_config = None
    
    @property
    def brands_config(self) -> dict:
        """Lazy load brands config"""
        if self._brands_config is None:
            self._brands_config = load_brands_config()
        return self._brands_config
    
    @property
    def available_brands(self) -> list:
        """Get list of available phone brands"""
        return list(self.brands_config.keys())
    
    @property
    def phone_error_categories(self) -> dict:
        """Lazy load phone error categories"""
        if self._phone_errors_config is None:
            self._phone_errors_config = load_phone_errors()
        return self._phone_errors_config
    
    # Static properties for simple config values
    @property
    def database_path(self):
        return DATABASE_PATH
    
    @property
    def icon_paths(self):
        return ICON_PATHS
    
    @property
    def password_hash_method(self):
        return PASSWORD_HASH_METHOD
    
    # Add other properties as needed...
    
    def get_brand_models(self, brand: str) -> list:
        """Get models for a specific brand"""
        return self.brands_config.get(brand, [])
    
    def get_error_category_errors(self, category: str) -> list:
        """Get errors for a specific category"""
        return self.phone_error_categories.get(category, [])

# Create singleton instance
config_manager = ConfigManager()