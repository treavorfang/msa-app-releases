"""InvoiceController - Bridge between UI and InvoiceService."""

from PySide6.QtCore import QObject, Signal
from typing import List, Optional
from dtos.invoice_dto import InvoiceDTO
from core.event_bus import EventBus
from core.events import InvoiceCreatedEvent, InvoiceUpdatedEvent, InvoiceDeletedEvent


class InvoiceController(QObject):
    """Controller for Invoice management."""
    
    # Signals now emit DTOs
    invoice_created = Signal(object)
    invoice_updated = Signal(object)
    invoice_deleted = Signal(int)
    item_added = Signal(int)  # invoice_id
    item_removed = Signal(int)  # item_id
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.invoice_service = container.invoice_service
        self.current_user = getattr(container, 'current_user', None) # Get user from container if available
        
    def create_invoice(self, invoice_data: dict, items: List[dict] = None) -> Optional[InvoiceDTO]:
        """Create a new invoice, optionally with items."""
        invoice = self.invoice_service.create_invoice(
            invoice_data, 
            items=items,
            current_user=self.current_user
        )
        if invoice:
            self.invoice_created.emit(invoice)
            EventBus.publish(InvoiceCreatedEvent(invoice.id))
        return invoice
        
    def get_invoice(self, invoice_id: int) -> Optional[InvoiceDTO]:
        """Get an invoice including its items."""
        return self.invoice_service.get_invoice(invoice_id)
        
    def update_invoice(self, invoice_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[InvoiceDTO]:
        """Update an invoice."""
        user = current_user or self.current_user
        invoice = self.invoice_service.update_invoice(
            invoice_id, 
            update_data, 
            current_user=user,
            ip_address=ip_address
        )
        if invoice:
            self.invoice_updated.emit(invoice)
            EventBus.publish(InvoiceUpdatedEvent(invoice.id))
        return invoice
        
    def delete_invoice(self, invoice_id: int) -> bool:
        """Delete an invoice."""
        success = self.invoice_service.delete_invoice(
            invoice_id, 
            current_user=self.current_user
        )
        if success:
            self.invoice_deleted.emit(invoice_id)
            EventBus.publish(InvoiceDeletedEvent(invoice_id))
        return success
        
    def list_invoices(self, branch_id: Optional[int] = None) -> List[InvoiceDTO]:
        """List all invoices."""
        return self.invoice_service.list_invoices(branch_id)
        
    def search_invoices(self, search_term: str) -> List[InvoiceDTO]:
        """Search invoices."""
        return self.invoice_service.search_invoices(search_term)
        
    def add_invoice_item(self, invoice_id: int, item_data: dict) -> bool:
        """Add an item to an invoice."""
        success = self.invoice_service.add_invoice_item(
            invoice_id, 
            item_data, 
            current_user=self.current_user
        )
        if success:
            self.item_added.emit(invoice_id)
            # Maybe trigger update signal to refresh UI amount?
            # Handled by getting updated invoice in UI usually
        return success
        
    def remove_invoice_item(self, item_id: int) -> bool:
        """Remove an item from an invoice."""
        success = self.invoice_service.remove_invoice_item(
            item_id, 
            current_user=self.current_user
        )
        if success:
            self.item_removed.emit(item_id)
        return success
        
    def get_customer_balance_info(self, customer_id: int) -> dict:
        """Get financial balance for a customer."""
        return self.invoice_service.get_customer_balance_info(customer_id)