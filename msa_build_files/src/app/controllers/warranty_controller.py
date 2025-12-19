"""WarrantyController - Bridge between UI and WarrantyService."""

from PySide6.QtCore import QObject, Signal
from typing import List, Optional
from dtos.warranty_dto import WarrantyDTO


class WarrantyController(QObject):
    """Controller for Warranty management."""
    
    # Signals now emit DTOs
    warranty_created = Signal(object)
    warranty_updated = Signal(object)
    warranty_deleted = Signal(int)
    status_checked = Signal(int, str)  # warranty_id, status
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.warranty_service = container.warranty_service
        self.current_user = getattr(container, 'current_user', None)
        
    def create_warranty(self, warranty_data: dict) -> Optional[WarrantyDTO]:
        """Create a new warranty."""
        warranty = self.warranty_service.create_warranty(
            warranty_data, 
            current_user=self.current_user
        )
        if warranty:
            self.warranty_created.emit(warranty)
        return warranty
        
    def get_warranty(self, warranty_id: int) -> Optional[WarrantyDTO]:
        """Get a warranty by ID."""
        return self.warranty_service.get_warranty(warranty_id)
        
    def update_warranty(self, warranty_id: int, update_data: dict) -> Optional[WarrantyDTO]:
        """Update a warranty."""
        warranty = self.warranty_service.update_warranty(
            warranty_id, 
            update_data, 
            current_user=self.current_user
        )
        if warranty:
            self.warranty_updated.emit(warranty)
        return warranty
        
    def delete_warranty(self, warranty_id: int) -> bool:
        """Delete a warranty."""
        success = self.warranty_service.delete_warranty(
            warranty_id, 
            current_user=self.current_user
        )
        if success:
            self.warranty_deleted.emit(warranty_id)
        return success
        
    def get_warranties_for_item(self, item_type: str, item_id: int) -> List[WarrantyDTO]:
        """Get warranties for an item."""
        return self.warranty_service.get_warranties_for_item(item_type, item_id)
        
    def check_warranty_status(self, warranty_id: int) -> str:
        """Check status."""
        status = self.warranty_service.check_warranty_status(warranty_id)
        self.status_checked.emit(warranty_id, status)
        return status
        
    def get_expiring_warranties(self, days: int = 30) -> List[WarrantyDTO]:
        """Get expiring warranties."""
        return self.warranty_service.get_expiring_warranties(days)