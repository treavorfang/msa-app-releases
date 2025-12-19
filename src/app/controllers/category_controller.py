# src/app/controllers/category_controller.py
from PySide6.QtCore import QObject, Signal
from typing import List, Optional
from dtos.category_dto import CategoryDTO

class CategoryController(QObject):
    category_created = Signal(object)  # Emits CategoryDTO
    category_updated = Signal(object)  # Emits CategoryDTO
    category_deleted = Signal(int)
    category_restored = Signal(int)
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.category_service = container.category_service
        
    def create_category(self, category_data: dict, current_user=None, ip_address=None) -> Optional[CategoryDTO]:
        category = self.category_service.create_category(category_data, current_user, ip_address)
        if category:
            self.category_created.emit(category)
        return category
        
    def get_category(self, category_id: int) -> Optional[CategoryDTO]:
        return self.category_service.get_category(category_id)
        
    def update_category(self, category_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[CategoryDTO]:
        category = self.category_service.update_category(category_id, update_data, current_user, ip_address)
        if category:
            self.category_updated.emit(category)
        return category
        
    def delete_category(self, category_id: int, current_user=None, ip_address=None) -> bool:
        success = self.category_service.delete_category(category_id, current_user, ip_address)
        if success:
            self.category_deleted.emit(category_id)
        return success
        
    def list_categories(self, include_inactive: bool = False, include_deleted: bool = False) -> List[CategoryDTO]:
        return self.category_service.list_categories(include_inactive, include_deleted)
        
    def search_categories(self, search_term: str, include_deleted: bool = False) -> List[CategoryDTO]:
        return self.category_service.search_categories(search_term, include_deleted)
        
    def restore_category(self, category_id: int, current_user=None, ip_address=None) -> bool:
        success = self.category_service.restore_category(category_id, current_user, ip_address)
        if success:
            self.category_restored.emit(category_id)
        return success