# src/app/interfaces/ipurchase_order_service.py
from abc import ABC, abstractmethod
from typing import Optional, List
from dtos.purchase_order_dto import PurchaseOrderDTO

class IPurchaseOrderService(ABC):
    @abstractmethod
    def create_purchase_order(self, po_data: dict, items: List[dict] = None, current_user=None, ip_address=None) -> PurchaseOrderDTO:
        pass
        
    @abstractmethod
    def get_purchase_order(self, po_id: int) -> Optional[PurchaseOrderDTO]:
        pass
        
    @abstractmethod
    def update_purchase_order(self, po_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[PurchaseOrderDTO]:
        pass
        
    @abstractmethod
    def delete_purchase_order(self, po_id: int, current_user=None, ip_address=None) -> bool:
        pass
        
    @abstractmethod
    def list_purchase_orders(self, status: Optional[str] = None, branch_id: Optional[int] = None) -> List[PurchaseOrderDTO]:
        pass
        
    @abstractmethod
    def search_purchase_orders(self, search_term: str) -> List[PurchaseOrderDTO]:
        pass
        
    @abstractmethod
    def update_status(self, po_id: int, new_status: str, current_user=None, ip_address=None) -> Optional[PurchaseOrderDTO]:
        pass