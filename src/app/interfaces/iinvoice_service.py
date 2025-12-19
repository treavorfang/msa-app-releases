# src/app/interfaces/iinvoice_service.py
from abc import ABC, abstractmethod
from typing import Optional, List
from dtos.invoice_dto import InvoiceDTO

class IInvoiceService(ABC):
    @abstractmethod
    def create_invoice(self, invoice_data: dict, items: List[dict] = None, current_user=None, ip_address=None) -> InvoiceDTO:
        pass
        
    @abstractmethod
    def get_invoice(self, invoice_id: int) -> Optional[InvoiceDTO]:
        pass
        
    @abstractmethod
    def update_invoice(self, invoice_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[InvoiceDTO]:
        pass
        
    @abstractmethod
    def delete_invoice(self, invoice_id: int, current_user=None, ip_address=None) -> bool:
        pass
        
    @abstractmethod
    def list_invoices(self, branch_id: Optional[int] = None) -> List[InvoiceDTO]:
        pass
        
    @abstractmethod
    def search_invoices(self, search_term: str) -> List[InvoiceDTO]:
        pass
        
    @abstractmethod
    def add_invoice_item(self, invoice_id: int, item_data: dict, current_user=None, ip_address=None) -> bool:
        pass
        
    @abstractmethod
    def remove_invoice_item(self, item_id: int, current_user=None, ip_address=None) -> bool:
        pass