"""PurchaseOrderItem Repository - Purchase Order Items Data Access Layer.

This repository handles all database operations for PurchaseOrderItem entities.
Manages line items on purchase orders.
"""

from typing import Optional, List
from models.purchase_order_item import PurchaseOrderItem


class PurchaseOrderItemRepository:
    """Repository for PurchaseOrderItem data access operations."""
    
    def create(self, item_data: dict) -> PurchaseOrderItem:
        """Create a new purchase order item."""
        return PurchaseOrderItem.create(**item_data)
    
    def get(self, item_id: int) -> Optional[PurchaseOrderItem]:
        """Get purchase order item by ID."""
        try:
            return PurchaseOrderItem.get_by_id(item_id)
        except PurchaseOrderItem.DoesNotExist:
            return None
    
    def update(self, item_id: int, update_data: dict) -> Optional[PurchaseOrderItem]:
        """Update purchase order item details."""
        try:
            item = PurchaseOrderItem.get_by_id(item_id)
            for key, value in update_data.items():
                setattr(item, key, value)
            item.save()
            return item
        except PurchaseOrderItem.DoesNotExist:
            return None
    
    def delete(self, item_id: int) -> bool:
        """Delete purchase order item by ID."""
        try:
            item = PurchaseOrderItem.get_by_id(item_id)
            item.delete_instance()
            return True
        except PurchaseOrderItem.DoesNotExist:
            return False
    
    def get_by_po(self, po_id: int) -> List[PurchaseOrderItem]:
        """Get all items for a specific purchase order."""
        return list(PurchaseOrderItem.select().where(PurchaseOrderItem.purchase_order == po_id))
