# src/app/interfaces/icategory_service.py
from abc import ABC, abstractmethod
from models.category import Category

class ICategoryService(ABC):
    @abstractmethod
    def create_category(self, category_data: dict) -> Category:
        pass
        
    @abstractmethod
    def get_category(self, category_id: int) -> Category:
        pass
        
    @abstractmethod
    def update_category(self, category_id: int, update_data: dict) -> Category:
        pass
        
    @abstractmethod
    def delete_category(self, category_id: int) -> bool:
        pass
        
    @abstractmethod
    def list_categories(self, include_inactive: bool = False) -> list[Category]:
        pass
        
    @abstractmethod
    def search_categories(self, search_term: str) -> list[Category]:
        pass