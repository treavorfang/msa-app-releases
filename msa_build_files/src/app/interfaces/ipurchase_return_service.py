"""IPurchaseReturnService - Interface for Purchase Return Service."""

from abc import ABC, abstractmethod
from typing import List, Optional
from dtos.purchase_return_dto import PurchaseReturnDTO
from dtos.purchase_return_item_dto import PurchaseReturnItemDTO

class IPurchaseReturnService(ABC):
    @abstractmethod
    def create_return(self, return_data: dict, items: List[dict] = None, current_user=None, ip_address=None) -> PurchaseReturnDTO:
        pass
        
    @abstractmethod
    def get_return(self, return_id: int) -> Optional[PurchaseReturnDTO]:
        pass
        
    @abstractmethod
    def update_return(self, return_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[PurchaseReturnDTO]:
        pass

    @abstractmethod
    def delete_return(self, return_id: int, current_user=None, ip_address=None) -> bool:
        pass
        
    @abstractmethod
    def list_returns(self, status: Optional[str] = None) -> List[PurchaseReturnDTO]:
        pass
        
    @abstractmethod
    def search_returns(self, search_term: str) -> List[PurchaseReturnDTO]:
        pass
        
    @abstractmethod
    def approve_return(self, return_id: int, current_user=None, ip_address=None) -> Optional[PurchaseReturnDTO]:
        pass

    @abstractmethod
    def add_item(self, return_id: int, item_data: dict) -> Optional[PurchaseReturnItemDTO]:
        pass

    @abstractmethod
    def remove_item(self, item_id: int) -> bool:
        pass

    @abstractmethod
    def update_item(self, item_id: int, update_data: dict) -> Optional[PurchaseReturnItemDTO]:
        pass
