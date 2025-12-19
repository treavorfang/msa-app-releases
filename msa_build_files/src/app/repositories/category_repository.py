"""Category Repository - Category Data Access Layer.

This repository handles all database operations for Category entities.
Supports soft deletion and category management.
"""

from datetime import datetime
from typing import Optional, List
from peewee import fn
from models.category import Category


class CategoryRepository:
    """Repository for Category data access operations."""
    
    def create(self, category_data: dict) -> Category:
        """Create a new category."""
        return Category.create(**category_data)
    
    def get(self, category_id: int) -> Optional[Category]:
        """Get category by ID (excluding soft-deleted)."""
        try:
            return Category.get((Category.id == category_id) & (Category.deleted_at.is_null()))
        except Category.DoesNotExist:
            return None
    
    def update(self, category_id: int, update_data: dict) -> Optional[Category]:
        """Update category with new data."""
        try:
            category = Category.get((Category.id == category_id) & (Category.deleted_at.is_null()))
            for key, value in update_data.items():
                setattr(category, key, value)
            category.save()
            return category
        except Category.DoesNotExist:
            return None
    
    def delete(self, category_id: int, deleted_by_id: Optional[int] = None) -> bool:
        """Soft delete a category."""
        try:
            category = Category.get((Category.id == category_id) & (Category.deleted_at.is_null()))
            category.deleted_at = datetime.now()
            category.deleted_by = deleted_by_id
            category.is_active = False
            category.save()
            return True
        except Category.DoesNotExist:
            return False
    
    def list_all(self, include_inactive: bool = False, include_deleted: bool = False) -> List[Category]:
        """Get all categories with optional filters."""
        query = Category.select()
        
        if not include_deleted:
            query = query.where(Category.deleted_at.is_null())
        
        if not include_inactive and not include_deleted:
            query = query.where(Category.is_active == True)
        elif not include_inactive:
            query = query.where((Category.is_active == True) | (Category.deleted_at.is_null(False)))
        
        return list(query)
    
    def search(self, search_term: str, include_deleted: bool = False) -> List[Category]:
        """Search categories by name or description."""
        search_term = search_term.lower()
        query = Category.select().where(
            (fn.LOWER(Category.name).contains(search_term)) |
            (fn.LOWER(Category.description).contains(search_term))
        )
        
        if not include_deleted:
            query = query.where(Category.deleted_at.is_null())
        
        return list(query)
    
    def restore(self, category_id: int) -> bool:
        """Restore a soft-deleted category."""
        try:
            category = Category.get((Category.id == category_id) & (Category.deleted_at.is_null(False)))
            category.deleted_at = None
            category.deleted_by = None
            category.save()
            return True
        except Category.DoesNotExist:
            return False