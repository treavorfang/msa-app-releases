"""CategoryService - Category Management Business Logic.

This service manages categories for parts and products, supporting hierarchical structures.
It handles lifecycle operations and integrates with the audit system using DTOs.
"""

from typing import List, Optional
from interfaces.icategory_service import ICategoryService
from repositories.category_repository import CategoryRepository
from services.audit_service import AuditService
from dtos.category_dto import CategoryDTO


class CategoryService(ICategoryService):
    """Service class for Category operations."""
    
    def __init__(self, audit_service: AuditService):
        """Initialize CategoryService.
        
        Args:
            audit_service: Service for logging security/audit events
        """
        self.repository = CategoryRepository()
        self.audit_service = audit_service
        
    def create_category(self, category_data: dict, current_user=None, ip_address=None) -> CategoryDTO:
        """Create a new category."""
        category = self.repository.create(category_data)
        dto = CategoryDTO.from_model(category)
        
        self.audit_service.log_action(
            user=current_user,
            action="category_create",
            table_name="categories",
            new_data=dto.to_audit_dict(),
            ip_address=ip_address
        )
        return dto
        
    def get_category(self, category_id: int) -> Optional[CategoryDTO]:
        """Get a category by ID."""
        category = self.repository.get(category_id)
        return CategoryDTO.from_model(category) if category else None
        
    def update_category(self, category_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[CategoryDTO]:
        """Update an existing category."""
        old_category = self.repository.get(category_id)
        if not old_category:
            return None
            
        old_dto = CategoryDTO.from_model(old_category)
        
        category = self.repository.update(category_id, update_data)
        
        if category:
            new_dto = CategoryDTO.from_model(category)
            self.audit_service.log_action(
                user=current_user,
                action="category_update",
                table_name="categories",
                old_data=old_dto.to_audit_dict(),
                new_data=new_dto.to_audit_dict(),
                ip_address=ip_address
            )
            return new_dto
        return None
        
    def delete_category(self, category_id: int, current_user=None, ip_address=None) -> bool:
        """Soft delete a category."""
        category = self.repository.get(category_id)
        deleted_by_id = current_user.id if current_user else None
        
        if category:
            dto = CategoryDTO.from_model(category)
            success = self.repository.delete(category_id, deleted_by_id)
            
            if success:
                self.audit_service.log_action(
                    user=current_user,
                    action="category_delete",
                    table_name="categories",
                    old_data=dto.to_audit_dict(),
                    ip_address=ip_address
                )
            return success
        return False
        
    def list_categories(self, include_inactive: bool = False, include_deleted: bool = False) -> List[CategoryDTO]:
        """List all categories with optional filters."""
        categories = self.repository.list_all(include_inactive, include_deleted)
        return [CategoryDTO.from_model(c) for c in categories]
        
    def search_categories(self, search_term: str, include_deleted: bool = False) -> List[CategoryDTO]:
        """Search categories."""
        categories = self.repository.search(search_term, include_deleted)
        return [CategoryDTO.from_model(c) for c in categories]
        
    def restore_category(self, category_id: int, current_user=None, ip_address=None) -> bool:
        """Restore a soft-deleted category."""
        success = self.repository.restore(category_id)
        if success:
            self.audit_service.log_action(
                user=current_user,
                action="category_restore",
                table_name="categories",
                new_data={'category_id': category_id},
                ip_address=ip_address
            )
        return success