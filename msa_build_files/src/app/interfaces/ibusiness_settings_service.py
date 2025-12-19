"""IBusinessSettingsService - Interface for Settings Service."""

from abc import ABC, abstractmethod
from typing import Optional
from dtos.business_settings_dto import BusinessSettingsDTO

class IBusinessSettingsService(ABC):
    @abstractmethod
    def get_settings(self) -> Optional[BusinessSettingsDTO]:
        pass
        
    @abstractmethod
    def update_settings(self, settings_data: dict, current_user=None, ip_address=None) -> BusinessSettingsDTO:
        pass