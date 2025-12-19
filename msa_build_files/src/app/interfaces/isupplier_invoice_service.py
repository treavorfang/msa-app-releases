"""ISupplierInvoiceService - Interface for Supplier Invoice Service."""

from abc import ABC, abstractmethod
from typing import List, Optional
from dtos.supplier_invoice_dto import SupplierInvoiceDTO

class ISupplierInvoiceService(ABC):
    @abstractmethod
    def create_invoice(self, invoice_data: dict, current_user=None, ip_address=None) -> SupplierInvoiceDTO:
        pass
        
    @abstractmethod
    def get_invoice(self, invoice_id: int) -> Optional[SupplierInvoiceDTO]:
        pass

    @abstractmethod
    def get_invoice_by_number(self, invoice_number: str) -> Optional[SupplierInvoiceDTO]:
        pass
        
    @abstractmethod
    def update_invoice(self, invoice_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[SupplierInvoiceDTO]:
        pass
        
    @abstractmethod
    def delete_invoice(self, invoice_id: int, current_user=None, ip_address=None) -> bool:
        pass
        
    @abstractmethod
    def get_invoices_by_supplier(self, supplier_id: int) -> List[SupplierInvoiceDTO]:
        pass
        
    @abstractmethod
    def get_invoices_by_po(self, po_id: int) -> List[SupplierInvoiceDTO]:
        pass
        
    @abstractmethod
    def get_outstanding_invoices(self, supplier_id: Optional[int] = None) -> List[SupplierInvoiceDTO]:
        pass
        
    @abstractmethod
    def get_overdue_invoices(self, supplier_id: Optional[int] = None) -> List[SupplierInvoiceDTO]:
        pass
        
    @abstractmethod
    def get_outstanding_balance(self, supplier_id: int) -> float:
        pass
        
    @abstractmethod
    def get_all_invoices(self) -> List[SupplierInvoiceDTO]:
        pass
        
    @abstractmethod
    def list_invoices(self) -> List[SupplierInvoiceDTO]:
        pass
        
    @abstractmethod
    def get_invoices_by_status(self, status: str) -> List[SupplierInvoiceDTO]:
        pass
