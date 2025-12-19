# src/app/interfaces/isupplier_service.py
from abc import ABC, abstractmethod
from typing import List, Optional, Any
from dtos.supplier_dto import SupplierDTO

class ISupplierService(ABC):
    @abstractmethod
    def create_supplier(self, supplier_data: dict, current_user=None, ip_address=None) -> SupplierDTO:
        pass
        
    @abstractmethod
    def get_supplier(self, supplier_id: int) -> Optional[SupplierDTO]:
        pass
        
    @abstractmethod
    def update_supplier(self, supplier_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[SupplierDTO]:
        pass
        
    @abstractmethod
    def delete_supplier(self, supplier_id: int, current_user=None, ip_address=None) -> bool:
        pass
        
    @abstractmethod
    def list_suppliers(self, branch_id: Optional[int] = None) -> List[SupplierDTO]:
        pass
        
    @abstractmethod
    def search_suppliers(self, search_term: str) -> List[SupplierDTO]:
        pass