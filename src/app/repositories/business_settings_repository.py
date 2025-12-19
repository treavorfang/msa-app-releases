"""BusinessSettings Repository - Business Settings Data Access Layer.

This repository handles all database operations for BusinessSettings entities.
Manages application-wide business configuration (only one record).
"""

from typing import Optional
from models.business_settings import BusinessSettings


class BusinessSettingsRepository:
    """Repository for BusinessSettings data access operations."""
    
    def get_settings(self) -> Optional[BusinessSettings]:
        """Get the business settings record (singleton)."""
        try:
            return BusinessSettings.select().first()
        except BusinessSettings.DoesNotExist:
            return None
    
    def update_settings(self, settings_data: dict) -> Optional[BusinessSettings]:
        """Update or create the business settings record."""
        settings = self.get_settings()
        if settings:
            # Update existing settings
            for key, value in settings_data.items():
                setattr(settings, key, value)
            settings.save()
            return settings
        else:
            # Create new settings if none exist
            return BusinessSettings.create(**settings_data)
    
    def create_default_settings(self) -> BusinessSettings:
        """Create default business settings."""
        return BusinessSettings.create(
            business_name="My Business",
            business_phone=None,
            address=None,
            tax_id=None,
            logo_url=None,
            notes=None,
            default_tax_rate=0.0,
            create_by=None
        )