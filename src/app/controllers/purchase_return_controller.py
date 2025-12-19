"""PurchaseReturnController - Bridge between UI and PurchaseReturnService."""

from PySide6.QtCore import QObject, Signal
from typing import List, Optional
from dtos.purchase_return_dto import PurchaseReturnDTO
from dtos.purchase_return_item_dto import PurchaseReturnItemDTO


class PurchaseReturnController(QObject):
    """Controller for purchase return operations."""
    
    # Signals
    return_created = Signal(int)  # return_id
    return_updated = Signal(int)  # return_id
    return_approved = Signal(int)  # return_id
    credit_note_created = Signal(int)  # credit_note_id
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.return_service = container.purchase_return_service
        self.credit_service = container.credit_note_service
        self.current_user = getattr(container, 'current_user', None)
    
    def create_return(self, return_data: dict, items: List[dict] = None) -> Optional[PurchaseReturnDTO]:
        """Create a new purchase return."""
        purchase_return = self.return_service.create_return(
            return_data,
            items=items,
            current_user=self.current_user
        )
        if purchase_return:
            self.return_created.emit(purchase_return.id)
        return purchase_return
    
    def get_return(self, return_id: int) -> Optional[PurchaseReturnDTO]:
        """Get a return by ID."""
        return self.return_service.get_return(return_id)
    
    def update_return(self, return_id: int, update_data: dict) -> Optional[PurchaseReturnDTO]:
        """Update a return."""
        purchase_return = self.return_service.update_return(
            return_id,
            update_data,
            current_user=self.current_user
        )
        if purchase_return:
            self.return_updated.emit(return_id)
        return purchase_return
    
    def approve_return(self, return_id: int) -> Optional[PurchaseReturnDTO]:
        """Approve a return."""
        purchase_return = self.return_service.approve_return(
            return_id,
            current_user=self.current_user
        )
        if purchase_return:
            self.return_approved.emit(return_id)
            # Auto-generate credit note
            self.generate_credit_note(return_id)
        return purchase_return
    
    def add_item(self, return_id: int, item_data: dict) -> Optional[PurchaseReturnItemDTO]:
        """Add an item to a return."""
        return self.return_service.add_item(return_id, item_data)
    
    def remove_item(self, item_id: int) -> bool:
        """Remove an item from a return."""
        return self.return_service.remove_item(item_id)
    
    def update_item(self, item_id: int, update_data: dict) -> Optional[PurchaseReturnItemDTO]:
        """Update an item in a return."""
        return self.return_service.update_item(item_id, update_data)
    
    def get_items(self, return_id: int) -> List[PurchaseReturnItemDTO]:
        """Get all items for a return."""
        return self.return_service.get_items(return_id)
    
    def list_returns(self, status=None) -> List[PurchaseReturnDTO]:
        """List all returns."""
        return self.return_service.list_returns(status)
    
    def search_returns(self, search_term: str) -> List[PurchaseReturnDTO]:
        """Search returns."""
        return self.return_service.search_returns(search_term)
    
    def generate_credit_note(self, return_id: int):
        """Generate a credit note from a return."""
        # Note: CreditNoteService might not return DTOs yet
        credit_note = self.credit_service.generate_from_return(
            return_id,
            current_user=self.current_user
        )
        if credit_note:
            self.credit_note_created.emit(credit_note.id)
        return credit_note
    
    def apply_credit_to_invoice(self, credit_note_id: int, invoice_id: int, amount: float):
        """Apply credit to an invoice."""
        from decimal import Decimal
        return self.credit_service.apply_credit_to_invoice(
            credit_note_id,
            invoice_id,
            Decimal(str(amount)),
            current_user=self.current_user
        )
    
    def get_available_credits(self, supplier_id: int):
        """Get available credits for a supplier."""
        return self.credit_service.get_available_credits(supplier_id)
    
    def list_credit_notes(self, status=None):
        """List all credit notes."""
        return self.credit_service.list_credit_notes(status)
