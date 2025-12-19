"""BusinessSettingsService - Settings Management Logic.

This service manages business configuration using DTOs.
"""

from typing import Optional, Dict, Any
from interfaces.ibusiness_settings_service import IBusinessSettingsService
from repositories.business_settings_repository import BusinessSettingsRepository
from models.business_settings import BusinessSettings
from services.audit_service import AuditService
from dtos.business_settings_dto import BusinessSettingsDTO


class BusinessSettingsService(IBusinessSettingsService):
    """Service class for Business Settings operations."""
    
    def __init__(self, audit_service: AuditService):
        """Initialize BusinessSettingsService."""
        self.repository = BusinessSettingsRepository()
        self.audit_service = audit_service
        
    def get_settings(self) -> Optional[BusinessSettingsDTO]:
        """Get current business settings."""
        settings = self.repository.get_settings()
        if not settings:
            # Create default if missing (logic often in repo, calling it anyway)
            settings = self.repository.create_default_settings()
            
        return BusinessSettingsDTO.from_model(settings) if settings else None
        
    def update_settings(self, settings_data: dict, current_user=None, ip_address=None) -> BusinessSettingsDTO:
        """Update business settings."""
        # Ensure only 1 record exists usually, id=1
        current = self.repository.get_settings()
        if not current:
             current = self.repository.create_default_settings()
             
        old_dto = BusinessSettingsDTO.from_model(current)
        
        # Update using repo (likely updates first record)
        settings = self.repository.update_settings(settings_data)
        
        new_dto = BusinessSettingsDTO.from_model(settings)
        
        self.audit_service.log_action(
            user=current_user,
            action="settings_update",
            table_name="business_settings",
            old_data=old_dto.to_dict(),
            new_data=new_dto.to_dict(),
            ip_address=ip_address
        )
        return new_dto