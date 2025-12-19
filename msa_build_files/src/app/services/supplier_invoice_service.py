"""SupplierInvoiceService - Supplier Invoice Management Logic.

This service manages supplier invoices using DTOs.
"""

from typing import List, Optional, Any, Dict
from decimal import Decimal
from interfaces.isupplier_invoice_service import ISupplierInvoiceService
from models.supplier_invoice import SupplierInvoice
from repositories.supplier_invoice_repository import SupplierInvoiceRepository
from services.audit_service import AuditService
from dtos.supplier_invoice_dto import SupplierInvoiceDTO


class SupplierInvoiceService(ISupplierInvoiceService):
    """Service class for Supplier Invoice operations."""
    
    def __init__(self, audit_service: AuditService):
        """Initialize SupplierInvoiceService."""
        self._audit_service = audit_service
        self._repository = SupplierInvoiceRepository()
    
    def create_invoice(self, invoice_data: dict, current_user=None, ip_address=None) -> SupplierInvoiceDTO:
        """Create a new supplier invoice."""
        invoice = self._repository.create(invoice_data)
        dto = SupplierInvoiceDTO.from_model(invoice)
        
        self._audit_service.log_action(
            user=current_user,
            action="create",
            table_name="supplier_invoices",
            new_data=dto.to_audit_dict(),
            ip_address=ip_address
        )
        return dto
    
    def get_invoice(self, invoice_id: int) -> Optional[SupplierInvoiceDTO]:
        """Get an invoice by ID."""
        inv = self._repository.get(invoice_id)
        return SupplierInvoiceDTO.from_model(inv) if inv else None
    
    def get_invoice_by_number(self, invoice_number: str) -> Optional[SupplierInvoiceDTO]:
        """Get an invoice by invoice number."""
        inv = self._repository.get_by_invoice_number(invoice_number)
        return SupplierInvoiceDTO.from_model(inv) if inv else None
    
    def update_invoice(self, invoice_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[SupplierInvoiceDTO]:
        """Update an invoice."""
        old_inv = self._repository.get(invoice_id)
        if not old_inv:
            return None
        
        old_dto = SupplierInvoiceDTO.from_model(old_inv)
        invoice = self._repository.update(invoice_id, update_data)
        
        if invoice:
            new_dto = SupplierInvoiceDTO.from_model(invoice)
            self._audit_service.log_action(
                user=current_user,
                action="update",
                table_name="supplier_invoices",
                old_data=old_dto.to_audit_dict(),
                new_data=new_dto.to_audit_dict(),
                ip_address=ip_address
            )
            return new_dto
        return None
    
    def delete_invoice(self, invoice_id: int, current_user=None, ip_address=None) -> bool:
        """Delete an invoice."""
        inv = self._repository.get(invoice_id)
        if not inv:
            return False
            
        dto = SupplierInvoiceDTO.from_model(inv)
        success = self._repository.delete(invoice_id)
        
        if success:
            self._audit_service.log_action(
                user=current_user,
                action="delete",
                table_name="supplier_invoices",
                old_data=dto.to_audit_dict(),
                ip_address=ip_address
            )
        return success
    
    def get_invoices_by_supplier(self, supplier_id: int) -> List[SupplierInvoiceDTO]:
        """Get all invoices for a supplier."""
        invs = self._repository.get_by_supplier(supplier_id)
        return [SupplierInvoiceDTO.from_model(inv) for inv in invs]
    
    def get_invoices_by_po(self, po_id: int) -> List[SupplierInvoiceDTO]:
        """Get all invoices for a purchase order."""
        invs = self._repository.get_by_po(po_id)
        return [SupplierInvoiceDTO.from_model(inv) for inv in invs]
    
    def get_outstanding_invoices(self, supplier_id: Optional[int] = None) -> List[SupplierInvoiceDTO]:
        """Get all outstanding invoices."""
        invs = self._repository.get_outstanding(supplier_id)
        return [SupplierInvoiceDTO.from_model(inv) for inv in invs]
    
    def get_overdue_invoices(self, supplier_id: Optional[int] = None) -> List[SupplierInvoiceDTO]:
        """Get all overdue invoices."""
        invs = self._repository.get_overdue(supplier_id)
        return [SupplierInvoiceDTO.from_model(inv) for inv in invs]
    
    def get_outstanding_balance(self, supplier_id: int) -> float:
        """Calculate total outstanding balance for a supplier."""
        return self._repository.calculate_outstanding_balance(supplier_id)
    
    def get_all_invoices(self) -> List[SupplierInvoiceDTO]:
        """Get all invoices."""
        invs = self._repository.get_all()
        return [SupplierInvoiceDTO.from_model(inv) for inv in invs]
    
    def list_invoices(self) -> List[SupplierInvoiceDTO]:
        """List all invoices."""
        return self.get_all_invoices()
    
    def get_invoices_by_status(self, status: str) -> List[SupplierInvoiceDTO]:
        """Get invoices by status."""
        invs = list(SupplierInvoice.select().where(SupplierInvoice.status == status))
        return [SupplierInvoiceDTO.from_model(inv) for inv in invs]
