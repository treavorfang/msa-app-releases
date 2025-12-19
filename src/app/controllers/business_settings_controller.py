"""BusinessSettingsController - Bridge between UI and Service."""

from PySide6.QtCore import QObject, Signal
from typing import Optional
from dtos.business_settings_dto import BusinessSettingsDTO


class BusinessSettingsController(QObject):
    """Controller for Business Settings."""
    
    # Signals emit DTO
    settings_updated = Signal(object)
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.settings_service = container.business_settings_service
        self.current_user = getattr(container, 'current_user', None)
        
    def get_settings(self) -> Optional[BusinessSettingsDTO]:
        """Get settings."""
        return self.settings_service.get_settings()
        
    def update_settings(self, settings_data: dict) -> Optional[BusinessSettingsDTO]:
        """Update settings."""
        settings = self.settings_service.update_settings(
            settings_data, 
            current_user=self.current_user
        )
        if settings:
            self.settings_updated.emit(settings)
        return settings
        
    def get_tax_rate(self) -> float:
        """Get tax rate as float."""
        settings = self.get_settings()
        if settings:
            return float(settings.default_tax_rate)
        return 0.0