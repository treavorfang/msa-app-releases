"""PurchaseOrder Repository - Procurement Data Access Layer.

This repository handles all database operations for PurchaseOrder entities.
Features include ordering, status tracking, and supplier management.
"""

from typing import Optional, List
from peewee import fn
from models.purchase_order import PurchaseOrder


class PurchaseOrderRepository:
    """Repository for PurchaseOrder data access operations."""
    
    def create(self, po_data: dict) -> PurchaseOrder:
        """Create a new purchase order."""
        return PurchaseOrder.create(**po_data)
    
    def get(self, po_id: int) -> Optional[PurchaseOrder]:
        """Get purchase order by ID."""
        try:
            return PurchaseOrder.get_by_id(po_id)
        except PurchaseOrder.DoesNotExist:
            return None
    
    def update(self, po_id: int, update_data: dict) -> Optional[PurchaseOrder]:
        """Update purchase order details."""
        try:
            po = PurchaseOrder.get_by_id(po_id)
            for key, value in update_data.items():
                setattr(po, key, value)
            po.save()
            return po
        except PurchaseOrder.DoesNotExist:
            return None
    
    def delete(self, po_id: int) -> bool:
        """Delete purchase order by ID."""
        try:
            po = PurchaseOrder.get_by_id(po_id)
            po.delete_instance()
            return True
        except PurchaseOrder.DoesNotExist:
            return False
    
    def list_all(self, status: Optional[str] = None, branch_id: Optional[int] = None) -> List[PurchaseOrder]:
        """Get all purchase orders, optionally filtered by status and branch."""
        query = PurchaseOrder.select()
        if status:
            query = query.where(PurchaseOrder.status == status)
        if branch_id:
            query = query.where(PurchaseOrder.branch == branch_id)
        return list(query)
    
    def list_for_supplier(self, supplier_id: int) -> List[PurchaseOrder]:
        """Get all purchase orders for a supplier."""
        return list(PurchaseOrder.select().where(PurchaseOrder.supplier == supplier_id))

    def search(self, search_term: str) -> List[PurchaseOrder]:
        """Search purchase orders by number or notes."""
        search_term = search_term.lower()
        return list(PurchaseOrder.select().where(
            (fn.LOWER(PurchaseOrder.po_number).contains(search_term)) |
            (fn.LOWER(PurchaseOrder.notes).contains(search_term))
        ))