"""InvoiceItem Repository - Invoice Items Data Access Layer.

This repository handles all database operations for InvoiceItem entities.
Manages line items on invoices.
"""

from typing import Optional
from models.invoice_item import InvoiceItem


class InvoiceItemRepository:
    """Repository for InvoiceItem data access operations."""
    
    def create(self, item_data: dict) -> InvoiceItem:
        """Create a new invoice item."""
        return InvoiceItem.create(**item_data)
    
    def get(self, item_id: int) -> Optional[InvoiceItem]:
        """Get invoice item by ID."""
        try:
            return InvoiceItem.get_by_id(item_id)
        except InvoiceItem.DoesNotExist:
            return None
    
    def update(self, item_id: int, update_data: dict) -> Optional[InvoiceItem]:
        """Update invoice item details."""
        try:
            item = InvoiceItem.get_by_id(item_id)
            for key, value in update_data.items():
                setattr(item, key, value)
            item.save()
            return item
        except InvoiceItem.DoesNotExist:
            return None
    
    def delete(self, item_id: int) -> bool:
        """Delete invoice item by ID."""
        try:
            item = InvoiceItem.get_by_id(item_id)
            item.delete_instance()
            return True
        except InvoiceItem.DoesNotExist:
            return False