"""InvoiceService - Invoice Management Business Logic.

This service manages invoice entities and returns DTOs.
"""

from typing import List, Optional, Dict, Any
from interfaces.iinvoice_service import IInvoiceService
from repositories.invoice_repository import InvoiceRepository
from repositories.invoice_item_repository import InvoiceItemRepository
from models.invoice import Invoice
from models.invoice_item import InvoiceItem
from services.audit_service import AuditService
from dtos.invoice_dto import InvoiceDTO


class InvoiceService(IInvoiceService):
    """Service class for Invoice operations."""
    
    def __init__(self, audit_service: AuditService):
        """Initialize InvoiceService.
        
        Args:
            audit_service: Service for logging security/audit events
        """
        self.invoice_repo = InvoiceRepository()
        self.item_repo = InvoiceItemRepository()
        self.audit_service = audit_service
        
    def create_invoice(self, invoice_data: dict, items: List[dict] = None, current_user=None, ip_address=None) -> InvoiceDTO:
        """Create a new invoice, optionally with items."""
        # Auto-assign to Main Branch (ID=1) if not specified
        if 'branch_id' not in invoice_data or invoice_data['branch_id'] is None:
            invoice_data['branch_id'] = 1
        
        invoice = self.invoice_repo.create(invoice_data)
        
        # Automate Device Status: Invoice creation implies device is returned to customer
        if invoice.device:
            invoice.device.status = 'returned'
            invoice.device.save()
        
        # Handle initial items if provided
        if items:
            for item_data in items:
                item_data['invoice_id'] = invoice.id
                self.item_repo.create(item_data)
        
        # Reload to get items if needed, or construct DTO (items might be missing if no reload)
        # Assuming repo.get fetches items eagerly or lazily when accessed
        
        dto = InvoiceDTO.from_model(invoice)
        
        self.audit_service.log_action(
            user=current_user,
            action="invoice_create",
            table_name="invoices",
            new_data=dto.to_audit_dict(),
            ip_address=ip_address
        )
        return dto
        
    def get_invoice(self, invoice_id: int) -> Optional[InvoiceDTO]:
        """Get an invoice by ID."""
        invoice = self.invoice_repo.get(invoice_id)
        return InvoiceDTO.from_model(invoice) if invoice else None
        
    def update_invoice(self, invoice_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[InvoiceDTO]:
        """Update an existing invoice."""
        old_invoice = self.invoice_repo.get(invoice_id)
        if not old_invoice:
            return None
            
        old_dto = InvoiceDTO.from_model(old_invoice)
        
        invoice = self.invoice_repo.update(invoice_id, update_data)
        
        if invoice:
            new_dto = InvoiceDTO.from_model(invoice)
            self.audit_service.log_action(
                user=current_user,
                action="invoice_update",
                table_name="invoices",
                old_data=old_dto.to_audit_dict(),
                new_data=new_dto.to_audit_dict(),
                ip_address=ip_address
            )
            return new_dto
        return None
        
    def delete_invoice(self, invoice_id: int, current_user=None, ip_address=None) -> bool:
        """Soft delete an invoice."""
        invoice = self.invoice_repo.get(invoice_id)
        if not invoice:
            return False
            
        dto = InvoiceDTO.from_model(invoice)
        success = self.invoice_repo.delete(invoice_id)
        
        if success:
            self.audit_service.log_action(
                user=current_user,
                action="invoice_delete",
                table_name="invoices",
                old_data=dto.to_audit_dict(),
                ip_address=ip_address
            )
        return success
        
    def list_invoices(self, branch_id: Optional[int] = None) -> List[InvoiceDTO]:
        """List all invoices, optionally filtered by branch."""
        invoices = self.invoice_repo.list_all(branch_id)
        return [InvoiceDTO.from_model(inv) for inv in invoices]
        
    def search_invoices(self, search_term: str) -> List[InvoiceDTO]:
        """Search invoices by number or customer name."""
        invoices = self.invoice_repo.search(search_term)
        return [InvoiceDTO.from_model(inv) for inv in invoices]
        
    def add_invoice_item(self, invoice_id: int, item_data: dict, current_user=None, ip_address=None) -> bool:
        """Add a line item to an invoice."""
        # Ensure item data has the correct invoice_id
        item_data['invoice_id'] = invoice_id
        
        item = self.item_repo.create(item_data)
        if item:
            self.audit_service.log_action(
                user=current_user,
                action="invoice_item_add",
                table_name="invoice_items",
                new_data={
                    'invoice_id': invoice_id,
                    'item_type': item.item_type,
                    'quantity': item.quantity,
                    'total': str(item.total)
                },
                ip_address=ip_address
            )
            return True
        return False
        
    def remove_invoice_item(self, item_id: int, current_user=None, ip_address=None) -> bool:
        """Remove a line item from an invoice."""
        item = self.item_repo.get(item_id)
        if not item:
            return False
            
        # Capture data before delete
        old_data = {
            'item_id': item.id,
            'invoice_id': item.invoice_id,
            'total': str(item.total)
        }
        
        success = self.item_repo.delete(item_id)
        if success:
            self.audit_service.log_action(
                user=current_user,
                action="invoice_item_remove",
                table_name="invoice_items",
                old_data=old_data,
                ip_address=ip_address
            )
        return success

    def get_customer_balance_info(self, customer_id: int) -> dict:
        """Calculate customer financial balance."""
        balance_info = {
            'total_invoices': 0,
            'total_owed': 0.0,
            'total_credit': 0.0,
            'balance': 0.0
        }
        
        invoices = self.invoice_repo.list_for_customer(customer_id)
        balance_info['total_invoices'] = len(invoices)
        
        for invoice in invoices:
            # Reusing the simplified logic: check if unpaid/partial
            # Note: A more robust system would sum actual payments vs total
            if invoice.payment_status in ['unpaid', 'partially_paid']:
                # For partial, we should check paid amount.
                # However, to match previous logic (roughly), we sum 'owed'.
                # Better approach: access invoice.get_balance_due() if on model?
                # The Invoice model HAS get_balance_due() method!
                due = invoice.get_balance_due()
                balance_info['total_owed'] += due
        
        balance_info['balance'] = balance_info['total_owed'] - balance_info['total_credit']
        return balance_info