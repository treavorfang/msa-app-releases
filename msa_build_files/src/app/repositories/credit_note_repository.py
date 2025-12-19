"""CreditNote Repository - Credit Note Data Access Layer.

This repository handles all database operations for CreditNote entities.
Features include credit management, tracking unused credits, and searches.
"""

from typing import List, Optional
from models.credit_note import CreditNote


class CreditNoteRepository:
    """Repository for CreditNote data access operations."""
    
    def create(self, data: dict) -> CreditNote:
        """Create a new credit note."""
        return CreditNote.create(**data)
    
    def get(self, credit_note_id: int) -> Optional[CreditNote]:
        """Get credit note by ID."""
        try:
            return CreditNote.get_by_id(credit_note_id)
        except CreditNote.DoesNotExist:
            return None
    
    def update(self, credit_note_id: int, data: dict) -> Optional[CreditNote]:
        """Update credit note details."""
        try:
            credit_note = CreditNote.get_by_id(credit_note_id)
            for key, value in data.items():
                setattr(credit_note, key, value)
            credit_note.save()
            return credit_note
        except CreditNote.DoesNotExist:
            return None
    
    def get_all(self) -> List[CreditNote]:
        """Get all credit notes."""
        return list(CreditNote.select())
    
    def get_by_credit_number(self, credit_note_number: str) -> Optional[CreditNote]:
        """Get credit note by number."""
        try:
            return CreditNote.get(CreditNote.credit_note_number == credit_note_number)
        except CreditNote.DoesNotExist:
            return None
    
    def get_by_return(self, return_id: int) -> List[CreditNote]:
        """Get all credit notes for a specific return."""
        return list(CreditNote.select().where(CreditNote.purchase_return == return_id))
    
    def get_by_supplier(self, supplier_id: int) -> List[CreditNote]:
        """Get all credit notes for a specific supplier."""
        from models.purchase_return import PurchaseReturn
        from models.purchase_order import PurchaseOrder
        return list(
            CreditNote
            .select()
            .join(PurchaseReturn)
            .join(PurchaseOrder)
            .where(PurchaseOrder.supplier == supplier_id)
        )
    
    def get_available_credits(self, supplier_id: int) -> List[CreditNote]:
        """Get all available (unused) credit notes for a supplier."""
        from models.purchase_return import PurchaseReturn
        from models.purchase_order import PurchaseOrder
        return list(
            CreditNote
            .select()
            .join(PurchaseReturn)
            .join(PurchaseOrder)
            .where(
                (PurchaseOrder.supplier == supplier_id) &
                (CreditNote.remaining_credit > 0) &
                (CreditNote.status == 'pending')
            )
        )
    
    def get_by_status(self, status: str) -> List[CreditNote]:
        """Get credit notes by status."""
        return list(CreditNote.select().where(CreditNote.status == status))
