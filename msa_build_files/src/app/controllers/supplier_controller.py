"""SupplierController - Bridge between UI and SupplierService."""

from PySide6.QtCore import QObject, Signal
from typing import List, Optional
from dtos.supplier_dto import SupplierDTO


class SupplierController(QObject):
    """Controller for Supplier management."""
    
    # Signals now emit DTOs
    supplier_created = Signal(object) # Using object to avoid registration issues with custom types first
    supplier_updated = Signal(object)
    supplier_deleted = Signal(int)
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.supplier_service = container.supplier_service
        self.current_user = getattr(container, 'current_user', None) # Get user from container if available
        
    def create_supplier(self, supplier_data: dict) -> Optional[SupplierDTO]:
        """Create a new supplier."""
        supplier = self.supplier_service.create_supplier(
            supplier_data, 
            current_user=self.current_user
        )
        if supplier:
            self.supplier_created.emit(supplier)
        return supplier
        
    def get_supplier(self, supplier_id: int) -> Optional[SupplierDTO]:
        """Get a supplier by ID."""
        return self.supplier_service.get_supplier(supplier_id)
        
    def update_supplier(self, supplier_id: int, update_data: dict) -> Optional[SupplierDTO]:
        """Update a supplier."""
        supplier = self.supplier_service.update_supplier(
            supplier_id, 
            update_data, 
            current_user=self.current_user
        )
        if supplier:
            self.supplier_updated.emit(supplier)
        return supplier
        
    def delete_supplier(self, supplier_id: int) -> bool:
        """Delete a supplier."""
        success = self.supplier_service.delete_supplier(
            supplier_id, 
            current_user=self.current_user
        )
        if success:
            self.supplier_deleted.emit(supplier_id)
        return success
        
    def list_suppliers(self, branch_id: Optional[int] = None) -> List[SupplierDTO]:
        """List all suppliers."""
        return self.supplier_service.list_suppliers(branch_id)
        
    def search_suppliers(self, search_term: str) -> List[SupplierDTO]:
        """Search suppliers."""
        return self.supplier_service.search_suppliers(search_term)