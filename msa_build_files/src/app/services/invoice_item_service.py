"""InvoiceItemService - Invoice Line Item Logic.

This service manages individual line items on an invoice, specifically updates.
Creation and deletion are typically handled via the parent InvoiceService.
"""

from typing import Optional
from interfaces.iinvoice_item_service import IInvoiceItemService
from repositories.invoice_item_repository import InvoiceItemRepository
from models.invoice_item import InvoiceItem
from services.audit_service import AuditService


class InvoiceItemService(IInvoiceItemService):
    """Service class for Invoice Item operations."""
    
    def __init__(self, audit_service: AuditService):
        """Initialize InvoiceItemService.
        
        Args:
            audit_service: Service for logging security/audit events
        """
        self.repository = InvoiceItemRepository()
        self.audit_service = audit_service
        
    def get_invoice_item(self, item_id: int) -> Optional[InvoiceItem]:
        """Get an invoice item by ID."""
        return self.repository.get(item_id)
        
    def update_invoice_item(self, item_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[InvoiceItem]:
        """Update an invoice item (e.g. quantity or price).
        
        Args:
            item_id: ID to update
            update_data: New properties
            current_user: User performing update
            ip_address: Client IP
            
        Returns:
            Optional[InvoiceItem]: Updated item or None
        """
        old_item = self.repository.get(item_id)
        item = self.repository.update(item_id, update_data)
        
        if item and old_item:
            self.audit_service.log_action(
                user=current_user,
                action="invoice_item_update",
                table_name="invoice_items",
                old_data={
                    'quantity': old_item.quantity,
                    'unit_price': str(old_item.unit_price),
                    'total': str(old_item.total)
                },
                new_data={
                    'quantity': item.quantity,
                    'unit_price': str(item.unit_price),
                    'total': str(item.total)
                },
                ip_address=ip_address
            )
        return item