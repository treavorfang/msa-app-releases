"""PurchaseReturn Repository - Purchase Return Data Access Layer.

This repository handles all database operations for PurchaseReturn entities.
Features include return creation, status tracking, and various lookups.
"""

from typing import List, Optional
from models.purchase_return import PurchaseReturn


class PurchaseReturnRepository:
    """Repository for PurchaseReturn data access operations."""
    
    def create(self, data: dict) -> PurchaseReturn:
        """Create a new purchase return."""
        return PurchaseReturn.create(**data)
    
    def get(self, return_id: int) -> Optional[PurchaseReturn]:
        """Get a return by ID."""
        try:
            return PurchaseReturn.get_by_id(return_id)
        except PurchaseReturn.DoesNotExist:
            return None
    
    def update(self, return_id: int, data: dict) -> Optional[PurchaseReturn]:
        """Update a return entry."""
        try:
            purchase_return = PurchaseReturn.get_by_id(return_id)
            for key, value in data.items():
                setattr(purchase_return, key, value)
            purchase_return.save()
            return purchase_return
        except PurchaseReturn.DoesNotExist:
            return None
    
    def get_all(self) -> List[PurchaseReturn]:
        """Get all returns."""
        return list(PurchaseReturn.select())
    
    def get_by_return_number(self, return_number: str) -> Optional[PurchaseReturn]:
        """Get a return by return number."""
        try:
            return PurchaseReturn.get(PurchaseReturn.return_number == return_number)
        except PurchaseReturn.DoesNotExist:
            return None
    
    def get_by_po(self, po_id: int) -> List[PurchaseReturn]:
        """Get all returns for a specific purchase order."""
        return list(PurchaseReturn.select().where(PurchaseReturn.purchase_order == po_id))
    
    def get_by_status(self, status: str) -> List[PurchaseReturn]:
        """Get all returns with a specific status."""
        return list(PurchaseReturn.select().where(PurchaseReturn.status == status))
    
    def get_by_supplier(self, supplier_id: int) -> List[PurchaseReturn]:
        """Get all returns for a specific supplier via PurchaseOrder."""
        from models.purchase_order import PurchaseOrder
        return list(
            PurchaseReturn
            .select()
            .join(PurchaseOrder)
            .where(PurchaseOrder.supplier == supplier_id)
        )
    
    def search(self, search_term: str) -> List[PurchaseReturn]:
        """Search returns by return number or notes."""
        return list(
            PurchaseReturn.select().where(
                (PurchaseReturn.return_number.contains(search_term)) |
                (PurchaseReturn.notes.contains(search_term))
            )
        )
