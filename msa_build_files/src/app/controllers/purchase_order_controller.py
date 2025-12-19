"""PurchaseOrderController - Bridge between UI and PurchaseOrderService."""

from PySide6.QtCore import QObject, Signal
from typing import List, Optional
from dtos.purchase_order_dto import PurchaseOrderDTO
from dtos.purchase_order_item_dto import PurchaseOrderItemDTO


class PurchaseOrderController(QObject):
    """Controller for PurchaseOrder management."""
    
    # Signals now emit DTOs
    po_created = Signal(object)
    po_updated = Signal(object)
    po_deleted = Signal(int)
    status_changed = Signal(int, str)  # po_id, new_status
    items_changed = Signal(int)  # po_id
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.po_service = container.purchase_order_service
        self.current_user = getattr(container, 'current_user', None)
        
    def create_purchase_order(self, po_data: dict, items: List[dict] = None) -> Optional[PurchaseOrderDTO]:
        """Create a new purchase order."""
        po = self.po_service.create_purchase_order(
            po_data, 
            items=items,
            current_user=self.current_user
        )
        if po:
            self.po_created.emit(po)
        return po
        
    def get_purchase_order(self, po_id: int) -> Optional[PurchaseOrderDTO]:
        """Get a purchase order."""
        return self.po_service.get_purchase_order(po_id)
        
    def update_purchase_order(self, po_id: int, update_data: dict) -> Optional[PurchaseOrderDTO]:
        """Update a purchase order."""
        po = self.po_service.update_purchase_order(
            po_id, 
            update_data, 
            current_user=self.current_user
        )
        if po:
            self.po_updated.emit(po)
        return po
        
    def delete_purchase_order(self, po_id: int) -> bool:
        """Delete a purchase order."""
        success = self.po_service.delete_purchase_order(
            po_id, 
            current_user=self.current_user
        )
        if success:
            self.po_deleted.emit(po_id)
        return success
        
    def list_purchase_orders(self, status: Optional[str] = None, branch_id: Optional[int] = None) -> List[PurchaseOrderDTO]:
        """List purchase orders."""
        return self.po_service.list_purchase_orders(status, branch_id)
        
    def search_purchase_orders(self, search_term: str) -> List[PurchaseOrderDTO]:
        """Search purchase orders."""
        return self.po_service.search_purchase_orders(search_term)
        
    def update_status(self, po_id: int, new_status: str) -> Optional[PurchaseOrderDTO]:
        """Update purchase order status."""
        po = self.po_service.update_status(
            po_id, 
            new_status, 
            current_user=self.current_user
        )
        if po:
            self.status_changed.emit(po_id, new_status)
        return po

    def add_item(self, po_id: int, item_data: dict) -> Optional[PurchaseOrderItemDTO]:
        """Add an item to a purchase order."""
        item = self.po_service.add_item(po_id, item_data)
        if item:
            self.items_changed.emit(po_id)
        return item

    def remove_item(self, item_id: int) -> bool:
        """Remove an item from a purchase order."""
        # Need to identify po_id before deletion to emit signal
        # Leveraging direct repo access for lookup (maintained legacy pattern)
        repo_item = self.po_service.item_repository.get(item_id)
        if repo_item:
            po_id = repo_item.purchase_order.id
            success = self.po_service.remove_item(item_id)
            if success:
                self.items_changed.emit(po_id)
            return success
        return False

    def update_item(self, item_id: int, update_data: dict) -> Optional[PurchaseOrderItemDTO]:
        """Update an item."""
        item = self.po_service.update_item(item_id, update_data)
        if item:
            self.items_changed.emit(item.purchase_order_id)
        return item

    def get_items(self, po_id: int) -> List[PurchaseOrderItemDTO]:
        """Get items for a purchase order."""
        return self.po_service.get_items(po_id)
        
    def get_supplier_balance_info(self, supplier_id: int) -> dict:
        """Get balance info for a supplier."""
        return self.po_service.get_supplier_balance_info(supplier_id)