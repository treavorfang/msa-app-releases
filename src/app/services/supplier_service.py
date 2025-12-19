"""SupplierService - Supplier Management Business Logic.

This service manages supplier entities and returns DTOs.
"""

from typing import List, Optional
from interfaces.isupplier_service import ISupplierService
from repositories.supplier_repository import SupplierRepository
from models.supplier import Supplier
from services.audit_service import AuditService
from dtos.supplier_dto import SupplierDTO


class SupplierService(ISupplierService):
    """Service class for Supplier operations."""
    
    def __init__(self, audit_service: AuditService):
        """Initialize SupplierService.
        
        Args:
            audit_service: Service for logging security/audit events
        """
        self.repository = SupplierRepository()
        self.audit_service = audit_service
        
    def create_supplier(self, supplier_data: dict, current_user=None, ip_address=None) -> SupplierDTO:
        """Create a new supplier."""
        # Auto-assign to Main Branch (ID=1) if not specified
        if 'branch_id' not in supplier_data or supplier_data['branch_id'] is None:
            supplier_data['branch_id'] = 1
        
        supplier = self.repository.create(supplier_data)
        dto = SupplierDTO.from_model(supplier)
        
        self.audit_service.log_action(
            user=current_user,
            action="supplier_create",
            table_name="suppliers",
            new_data=dto.to_audit_dict(),
            ip_address=ip_address
        )
        return dto
        
    def get_supplier(self, supplier_id: int) -> Optional[SupplierDTO]:
        """Get a supplier by ID."""
        supplier = self.repository.get(supplier_id)
        return SupplierDTO.from_model(supplier) if supplier else None
        
    def update_supplier(self, supplier_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[SupplierDTO]:
        """Update an existing supplier."""
        old_supplier = self.repository.get(supplier_id)
        if not old_supplier:
            return None
        
        old_dto = SupplierDTO.from_model(old_supplier)
        
        supplier = self.repository.update(supplier_id, update_data)
        
        if supplier:
            new_dto = SupplierDTO.from_model(supplier)
            self.audit_service.log_action(
                user=current_user,
                action="supplier_update",
                table_name="suppliers",
                old_data=old_dto.to_audit_dict(),
                new_data=new_dto.to_audit_dict(),
                ip_address=ip_address
            )
            return new_dto
        return None
        
    def delete_supplier(self, supplier_id: int, current_user=None, ip_address=None) -> bool:
        """Delete a supplier (soft delete recommended but calls repo delete)."""
        supplier = self.repository.get(supplier_id)
        if not supplier:
            return False
            
        dto = SupplierDTO.from_model(supplier)
        success = self.repository.delete(supplier_id)
        
        if success:
            self.audit_service.log_action(
                user=current_user,
                action="supplier_delete",
                table_name="suppliers",
                old_data=dto.to_audit_dict(),
                ip_address=ip_address
            )
        return success
        
    def list_suppliers(self, branch_id: Optional[int] = None) -> List[SupplierDTO]:
        """List all suppliers, optionally filtered by branch."""
        suppliers = self.repository.list_all(branch_id)
        return [SupplierDTO.from_model(s) for s in suppliers]
        
    def search_suppliers(self, search_term: str) -> List[SupplierDTO]:
        """Search suppliers by name, contact person, or email."""
        suppliers = self.repository.search(search_term)
        return [SupplierDTO.from_model(s) for s in suppliers]