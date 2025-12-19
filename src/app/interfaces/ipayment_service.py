"""IPaymentService - Interface for Payment Service."""

from abc import ABC, abstractmethod
from typing import Optional, List
from dtos.payment_dto import PaymentDTO

class IPaymentService(ABC):
    @abstractmethod
    def create_payment(self, payment_data: dict, current_user=None, ip_address=None) -> PaymentDTO:
        pass
        
    @abstractmethod
    def get_payment(self, payment_id: int) -> Optional[PaymentDTO]:
        pass
        
    @abstractmethod
    def update_payment(self, payment_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[PaymentDTO]:
        pass
        
    @abstractmethod
    def delete_payment(self, payment_id: int, current_user=None, ip_address=None) -> bool:
        pass
        
    @abstractmethod
    def get_payments_for_invoice(self, invoice_id: int) -> List[PaymentDTO]:
        pass
        
    @abstractmethod
    def get_total_paid_for_invoice(self, invoice_id: int) -> float:
        pass