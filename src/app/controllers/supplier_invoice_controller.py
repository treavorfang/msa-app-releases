"""SupplierInvoiceController - Bridge between UI and SupplierInvoiceService."""

from PySide6.QtCore import QObject, Signal
from typing import List, Optional
from dtos.supplier_invoice_dto import SupplierInvoiceDTO


class SupplierInvoiceController(QObject):
    """Controller for Supplier Invoice management."""
    
    # Signals
    invoice_created = Signal(object) # DTO
    invoice_updated = Signal(object) # DTO
    invoice_deleted = Signal(int)    # ID
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.service = container.supplier_invoice_service
        self.current_user = getattr(container, 'current_user', None)
        
    def create_invoice(self, invoice_data: dict) -> Optional[SupplierInvoiceDTO]:
        """Create a new supplier invoice."""
        invoice = self.service.create_invoice(
            invoice_data,
            current_user=self.current_user
        )
        if invoice:
            self.invoice_created.emit(invoice)
        return invoice
        
    def get_invoice(self, invoice_id: int) -> Optional[SupplierInvoiceDTO]:
        """Get an invoice."""
        return self.service.get_invoice(invoice_id)
        
    def get_invoice_by_number(self, invoice_number: str) -> Optional[SupplierInvoiceDTO]:
        """Get an invoice by number."""
        return self.service.get_invoice_by_number(invoice_number)
        
    def update_invoice(self, invoice_id: int, update_data: dict) -> Optional[SupplierInvoiceDTO]:
        """Update an invoice."""
        invoice = self.service.update_invoice(
            invoice_id,
            update_data,
            current_user=self.current_user
        )
        if invoice:
            self.invoice_updated.emit(invoice)
        return invoice
        
    def delete_invoice(self, invoice_id: int) -> bool:
        """Delete an invoice."""
        success = self.service.delete_invoice(
            invoice_id,
            current_user=self.current_user
        )
        if success:
            self.invoice_deleted.emit(invoice_id)
        return success
        
    def get_invoices_by_supplier(self, supplier_id: int) -> List[SupplierInvoiceDTO]:
        """Get invoices for supplier."""
        return self.service.get_invoices_by_supplier(supplier_id)
        
    def get_invoices_by_po(self, po_id: int) -> List[SupplierInvoiceDTO]:
        """Get invoices for PO."""
        return self.service.get_invoices_by_po(po_id)
        
    def get_outstanding_invoices(self, supplier_id: Optional[int] = None) -> List[SupplierInvoiceDTO]:
        """Get outstanding invoices."""
        return self.service.get_outstanding_invoices(supplier_id)
        
    def get_overdue_invoices(self, supplier_id: Optional[int] = None) -> List[SupplierInvoiceDTO]:
        """Get overdue invoices."""
        return self.service.get_overdue_invoices(supplier_id)
        
    def get_outstanding_balance(self, supplier_id: int) -> float:
        """Get outstanding balance."""
        return self.service.get_outstanding_balance(supplier_id)
        
    def get_all_invoices(self) -> List[SupplierInvoiceDTO]:
        """Get all invoices."""
        return self.service.get_all_invoices()
        
    def list_invoices(self) -> List[SupplierInvoiceDTO]:
        """List all invoices."""
        return self.service.list_invoices()
        
    def get_invoices_by_status(self, status: str) -> List[SupplierInvoiceDTO]:
        """Get invoices by status."""
        return self.service.get_invoices_by_status(status)
