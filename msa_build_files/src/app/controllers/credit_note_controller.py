"""CreditNoteController - Bridge between UI and CreditNoteService."""

from PySide6.QtCore import QObject, Signal
from typing import List, Optional
from decimal import Decimal
from dtos.credit_note_dto import CreditNoteDTO


class CreditNoteController(QObject):
    """Controller for Credit Note management."""
    
    # Signals
    credit_note_created = Signal(object)
    credit_note_updated = Signal(object)
    credit_note_deleted = Signal(int)
    credit_applied = Signal(int, float) # cn_id, amount
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.service = container.credit_note_service
        self.current_user = getattr(container, 'current_user', None)
        
    def create_credit_note(self, cn_data: dict) -> Optional[CreditNoteDTO]:
        """Create a new credit note."""
        cn = self.service.create_credit_note(cn_data, current_user=self.current_user)
        if cn:
            self.credit_note_created.emit(cn)
        return cn
        
    def get_credit_note(self, cn_id: int) -> Optional[CreditNoteDTO]:
        """Get a credit note."""
        return self.service.get_credit_note(cn_id)
        
    def update_credit_note(self, cn_id: int, update_data: dict) -> Optional[CreditNoteDTO]:
        """Update a credit note."""
        cn = self.service.update_credit_note(cn_id, update_data, current_user=self.current_user)
        if cn:
            self.credit_note_updated.emit(cn)
        return cn
        
    def delete_credit_note(self, cn_id: int) -> bool:
        """Delete a credit note."""
        success = self.service.delete_credit_note(cn_id, current_user=self.current_user)
        if success:
            self.credit_note_deleted.emit(cn_id)
        return success
        
    def generate_from_return(self, return_id: int) -> Optional[CreditNoteDTO]:
        """Generate from purchase return."""
        cn = self.service.generate_from_return(return_id, current_user=self.current_user)
        if cn:
            self.credit_note_created.emit(cn)
        return cn
        
    def apply_credit_to_invoice(self, cn_id: int, invoice_id: int, amount: float) -> bool:
        """Apply credit to an invoice."""
        success = self.service.apply_credit_to_invoice(
            cn_id, 
            invoice_id, 
            Decimal(str(amount)),
            current_user=self.current_user
        )
        if success:
            self.credit_applied.emit(cn_id, amount)
        return success
        
    def get_available_credits(self, supplier_id: int) -> List[CreditNoteDTO]:
        """Get available credits."""
        return self.service.get_available_credits(supplier_id)
        
    def list_credit_notes(self, status: Optional[str] = None) -> List[CreditNoteDTO]:
        """List credit notes."""
        return self.service.list_credit_notes(status)
