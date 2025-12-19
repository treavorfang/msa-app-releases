"""WarrantyService - Warranty Management Business Logic.

This service manages warranties using DTOs.
"""

from typing import List, Optional, Any, Dict
from datetime import datetime
from interfaces.iwarranty_service import IWarrantyService
from repositories.warranty_repository import WarrantyRepository
from models.warranty import Warranty
from services.audit_service import AuditService
from dtos.warranty_dto import WarrantyDTO


class WarrantyService(IWarrantyService):
    """Service class for Warranty operations."""
    
    def __init__(self, audit_service: AuditService):
        """Initialize WarrantyService."""
        self.repository = WarrantyRepository()
        self.audit_service = audit_service
        
    def create_warranty(self, warranty_data: dict, current_user=None, ip_address=None) -> WarrantyDTO:
        """Create a new warranty record."""
        warranty = self.repository.create(warranty_data)
        dto = WarrantyDTO.from_model(warranty)
        
        self.audit_service.log_action(
            user=current_user,
            action="warranty_create",
            table_name="warranties",
            new_data=dto.to_audit_dict(),
            ip_address=ip_address
        )
        return dto
        
    def get_warranty(self, warranty_id: int) -> Optional[WarrantyDTO]:
        """Get a warranty by ID."""
        warranty = self.repository.get(warranty_id)
        return WarrantyDTO.from_model(warranty) if warranty else None
        
    def update_warranty(self, warranty_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[WarrantyDTO]:
        """Update a warranty's details."""
        old_warranty = self.repository.get(warranty_id)
        if not old_warranty:
            return None
        
        old_dto = WarrantyDTO.from_model(old_warranty)
        warranty = self.repository.update(warranty_id, update_data)
        
        if warranty:
            new_dto = WarrantyDTO.from_model(warranty)
            self.audit_service.log_action(
                user=current_user,
                action="warranty_update",
                table_name="warranties",
                old_data=old_dto.to_audit_dict(),
                new_data=new_dto.to_audit_dict(),
                ip_address=ip_address
            )
            return new_dto
        return None
        
    def delete_warranty(self, warranty_id: int, current_user=None, ip_address=None) -> bool:
        """Delete a warranty."""
        warranty = self.repository.get(warranty_id)
        if not warranty:
            return False
            
        dto = WarrantyDTO.from_model(warranty)
        success = self.repository.delete(warranty_id)
        
        if success:
            self.audit_service.log_action(
                user=current_user,
                action="warranty_delete",
                table_name="warranties",
                old_data=dto.to_audit_dict(),
                ip_address=ip_address
            )
        return success
        
    def get_warranties_for_item(self, item_type: str, item_id: int) -> List[WarrantyDTO]:
        """Get warranties linked to a specific item."""
        warranties = self.repository.get_for_item(item_type, item_id)
        return [WarrantyDTO.from_model(w) for w in warranties]
        
    def check_warranty_status(self, warranty_id: int) -> str:
        """Check status and auto-expire if needed."""
        warranty = self.repository.get(warranty_id)
        if not warranty:
            return 'not_found'
            
        if warranty.status != 'active':
            return warranty.status
            
        if datetime.now() > warranty.end_date:
            warranty.status = 'expired'
            warranty.save()
            return 'expired'
            
        return 'active'
        
    def get_expiring_warranties(self, days: int = 30) -> List[WarrantyDTO]:
        """Get warranties expiring within N days."""
        warranties = self.repository.get_expiring_soon(days)
        return [WarrantyDTO.from_model(w) for w in warranties]