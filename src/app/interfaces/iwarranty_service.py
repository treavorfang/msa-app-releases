"""IWarrantyService - Interface for Warranty Service."""

from abc import ABC, abstractmethod
from typing import Optional, List
from dtos.warranty_dto import WarrantyDTO

class IWarrantyService(ABC):
    @abstractmethod
    def create_warranty(self, warranty_data: dict, current_user=None, ip_address=None) -> WarrantyDTO:
        pass
        
    @abstractmethod
    def get_warranty(self, warranty_id: int) -> Optional[WarrantyDTO]:
        pass
        
    @abstractmethod
    def update_warranty(self, warranty_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[WarrantyDTO]:
        pass
        
    @abstractmethod
    def delete_warranty(self, warranty_id: int, current_user=None, ip_address=None) -> bool:
        pass
        
    @abstractmethod
    def get_warranties_for_item(self, item_type: str, item_id: int) -> List[WarrantyDTO]:
        pass
        
    @abstractmethod
    def check_warranty_status(self, warranty_id: int) -> str:
        pass
        
    @abstractmethod
    def get_expiring_warranties(self, days: int = 30) -> List[WarrantyDTO]:
        pass