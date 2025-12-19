"""ICreditNoteService - Interface for Credit Note Service."""

from abc import ABC, abstractmethod
from typing import List, Optional
from decimal import Decimal
from dtos.credit_note_dto import CreditNoteDTO

class ICreditNoteService(ABC):
    @abstractmethod
    def create_credit_note(self, cn_data: dict, current_user=None, ip_address=None) -> CreditNoteDTO:
        pass
        
    @abstractmethod
    def get_credit_note(self, cn_id: int) -> Optional[CreditNoteDTO]:
        pass
        
    @abstractmethod
    def update_credit_note(self, cn_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[CreditNoteDTO]:
        pass
        
    @abstractmethod
    def delete_credit_note(self, cn_id: int, current_user=None, ip_address=None) -> bool:
        pass
        
    @abstractmethod
    def generate_from_return(self, return_id: int, current_user=None, ip_address=None) -> Optional[CreditNoteDTO]:
        pass
        
    @abstractmethod
    def apply_credit_to_invoice(self, cn_id: int, invoice_id: int, amount: Decimal, current_user=None, ip_address=None) -> bool:
        pass
        
    @abstractmethod
    def get_available_credits(self, supplier_id: int) -> List[CreditNoteDTO]:
        pass
        
    @abstractmethod
    def list_credit_notes(self, status: Optional[str] = None) -> List[CreditNoteDTO]:
        pass
        
    @abstractmethod
    def get_expiring_credits(self, days: int = 30) -> List[CreditNoteDTO]:
        pass
