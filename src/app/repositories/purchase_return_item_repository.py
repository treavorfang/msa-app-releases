"""PurchaseReturnItem Repository - Purchase Return Item Data Access Layer.

This repository handles all database operations for PurchaseReturnItem entities.
Manages line items in purchase returns.
"""

from typing import List, Optional
from models.purchase_return_item import PurchaseReturnItem


class PurchaseReturnItemRepository:
    """Repository for PurchaseReturnItem data access operations."""
    
    def create(self, data: dict) -> PurchaseReturnItem:
        """Create a new return item."""
        return PurchaseReturnItem.create(**data)
    
    def get(self, item_id: int) -> Optional[PurchaseReturnItem]:
        """Get an item by ID."""
        try:
            return PurchaseReturnItem.get_by_id(item_id)
        except PurchaseReturnItem.DoesNotExist:
            return None
    
    def delete(self, item_id: int) -> bool:
        """Delete an item by ID."""
        try:
            item = PurchaseReturnItem.get_by_id(item_id)
            item.delete_instance()
            return True
        except PurchaseReturnItem.DoesNotExist:
            return False
    
    def get_by_return(self, return_id: int) -> List[PurchaseReturnItem]:
        """Get all items for a specific return."""
        return list(
            PurchaseReturnItem.select().where(
                PurchaseReturnItem.purchase_return == return_id
            )
        )
    
    def get_by_part(self, part_id: int) -> List[PurchaseReturnItem]:
        """Get all return items for a specific part."""
        return list(
            PurchaseReturnItem.select().where(
                PurchaseReturnItem.part == part_id
            )
        )
