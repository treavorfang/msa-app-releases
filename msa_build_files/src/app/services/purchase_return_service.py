"""PurchaseReturnService - Procurement Return Business Logic.

This service manages purchase returns using DTOs.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from interfaces.ipurchase_return_service import IPurchaseReturnService
from repositories.purchase_return_repository import PurchaseReturnRepository
from repositories.purchase_return_item_repository import PurchaseReturnItemRepository
from models.purchase_return import PurchaseReturn
from models.purchase_return_item import PurchaseReturnItem
from services.audit_service import AuditService
from interfaces.ipart_service import IPartService
from dtos.purchase_return_dto import PurchaseReturnDTO
from dtos.purchase_return_item_dto import PurchaseReturnItemDTO


class PurchaseReturnService(IPurchaseReturnService):
    """Service class for Purchase Return operations."""
    
    def __init__(self, audit_service: Optional[AuditService] = None, part_service: Optional[IPartService] = None):
        """Initialize PurchaseReturnService."""
        self.repository = PurchaseReturnRepository()
        self.item_repository = PurchaseReturnItemRepository()
        self.audit_service = audit_service
        self.part_service = part_service
        
    def create_return(self, return_data: dict, items: List[dict] = None, current_user=None, ip_address=None) -> PurchaseReturnDTO:
        """Create a new purchase return."""
        # Generate return number if not provided
        if 'return_number' not in return_data:
            # Using count approach (simplistic but functional for now)
            return_count = PurchaseReturn.select().count()
            return_number = f"PR-{datetime.now().strftime('%Y%m%d')}-{return_count + 1:04d}"
            return_data['return_number'] = return_number
            
        return_data['created_by'] = current_user
        
        purchase_return = self.repository.create(return_data)
        
        if items:
            for item_data in items:
                item_data['purchase_return'] = purchase_return.id
                self.item_repository.create(item_data)
            self._update_return_total(purchase_return.id)
            # Fetch fresh
            purchase_return = self.repository.get(purchase_return.id)
            
        dto = PurchaseReturnDTO.from_model(purchase_return)
        
        if self.audit_service:
            self.audit_service.log_action(
                user=current_user,
                action="return_create",
                table_name="purchase_returns",
                new_data=dto.to_audit_dict(),
                ip_address=ip_address
            )
            
        return dto
        
    def get_return(self, return_id: int) -> Optional[PurchaseReturnDTO]:
        """Get a return by ID."""
        pr = self.repository.get(return_id)
        return PurchaseReturnDTO.from_model(pr) if pr else None
        
    def update_return(self, return_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[PurchaseReturnDTO]:
        """Update an existing return."""
        old_pr = self.repository.get(return_id)
        if not old_pr:
            return None
        
        old_dto = PurchaseReturnDTO.from_model(old_pr)
        purchase_return = self.repository.update(return_id, update_data)
        
        if purchase_return:
            new_dto = PurchaseReturnDTO.from_model(purchase_return)
            if self.audit_service:
                self.audit_service.log_action(
                    user=current_user,
                    action="return_update",
                    table_name="purchase_returns",
                    old_data=old_dto.to_audit_dict(),
                    new_data=new_dto.to_audit_dict(),
                    ip_address=ip_address
                )
            return new_dto
        return None
        
    def delete_return(self, return_id: int, current_user=None, ip_address=None) -> bool:
        """Delete a purchase return."""
        pr = self.repository.get(return_id)
        if not pr:
            return False
            
        dto = PurchaseReturnDTO.from_model(pr)
        success = self.repository.delete(return_id)
        
        if success and self.audit_service:
            self.audit_service.log_action(
                user=current_user,
                action="return_delete",
                table_name="purchase_returns",
                old_data=dto.to_audit_dict(),
                ip_address=ip_address
            )
        return success
        
    def list_returns(self, status: Optional[str] = None) -> List[PurchaseReturnDTO]:
        """List all returns, optionally filtered by status."""
        if status:
            prs = self.repository.get_by_status(status)
        else:
            prs = self.repository.get_all()
        return [PurchaseReturnDTO.from_model(pr) for pr in prs]
        
    def search_returns(self, search_term: str) -> List[PurchaseReturnDTO]:
        """Search returns."""
        prs = self.repository.search(search_term)
        return [PurchaseReturnDTO.from_model(pr) for pr in prs]
        
    def approve_return(self, return_id: int, current_user=None, ip_address=None) -> Optional[PurchaseReturnDTO]:
        """Approve a return and adjust inventory."""
        purchase_return = self.repository.get(return_id)
        if not purchase_return or purchase_return.status != 'draft':
            return None
            
        update_data = {
            'status': 'approved',
            'approved_by': current_user,
            'approved_at': datetime.now()
        }
        
        if self.part_service:
            items = self.item_repository.get_by_return(return_id)
            for item in items:
                self.part_service.update_stock(
                    item.part.id, 
                    -item.quantity,
                    reference_type='purchase_return',
                    reference_id=return_id,
                    notes=f"Return Approved {purchase_return.return_number}",
                    user=current_user
                )
                
        updated_pr = self.repository.update(return_id, update_data)
        
        if updated_pr:
            dto = PurchaseReturnDTO.from_model(updated_pr)
            if self.audit_service:
                self.audit_service.log_action(
                    user=current_user,
                    action="return_approve",
                    table_name="purchase_returns",
                    old_data={'return_id': return_id, 'status': 'draft'},
                    new_data={'status': 'approved'},
                    ip_address=ip_address
                )
            return dto
        return None
        
    def add_item(self, return_id: int, item_data: dict) -> Optional[PurchaseReturnItemDTO]:
        """Add an item to a return."""
        item_data['purchase_return'] = return_id
        item = self.item_repository.create(item_data)
        self._update_return_total(return_id)
        return PurchaseReturnItemDTO.from_model(item) if item else None
        
    def remove_item(self, item_id: int) -> bool:
        """Remove an item from a return."""
        item = self.item_repository.get(item_id)
        if item:
            return_id = item.purchase_return.id
            success = self.item_repository.delete(item_id)
            if success:
                self._update_return_total(return_id)
            return success
        return False
        
    def update_item(self, item_id: int, update_data: dict) -> Optional[PurchaseReturnItemDTO]:
        """Update an item in a return."""
        item = self.item_repository.update(item_id, update_data)
        if item:
            self._update_return_total(item.purchase_return.id)
            return PurchaseReturnItemDTO.from_model(item)
        return None
        
    def get_items(self, return_id: int) -> List[PurchaseReturnItemDTO]:
        """Get items for a return."""
        items = self.item_repository.get_by_return(return_id)
        return [PurchaseReturnItemDTO.from_model(item) for item in items]

    def _update_return_total(self, return_id: int):
        """Internal helper to update total."""
        items = self.item_repository.get_by_return(return_id)
        total = sum(float(item.total_cost) for item in items)
        self.repository.update(return_id, {'total_amount': total})
