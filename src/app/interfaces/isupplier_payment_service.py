"""ISupplierPaymentService - Interface for Supplier Payment Service."""

from abc import ABC, abstractmethod
from typing import List, Optional
from dtos.supplier_payment_dto import SupplierPaymentDTO

class ISupplierPaymentService(ABC):
    @abstractmethod
    def record_payment(self, payment_data: dict, current_user=None, ip_address=None) -> SupplierPaymentDTO:
        pass
        
    @abstractmethod
    def get_payment(self, payment_id: int) -> Optional[SupplierPaymentDTO]:
        pass
        
    @abstractmethod
    def update_payment(self, payment_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[SupplierPaymentDTO]:
        pass
        
    @abstractmethod
    def delete_payment(self, payment_id: int, current_user=None, ip_address=None) -> bool:
        pass
        
    @abstractmethod
    def get_payments_by_invoice(self, invoice_id: int) -> List[SupplierPaymentDTO]:
        pass
