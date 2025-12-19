"""Supplier Repository - Supplier Data Access Layer.

This repository handles all database operations for Supplier entities.
Features include supplier management and search capabilities.
"""

from typing import Optional, List
from peewee import fn
from models.supplier import Supplier


class SupplierRepository:
    """Repository for Supplier data access operations."""
    
    def create(self, supplier_data: dict) -> Supplier:
        """Create a new supplier."""
        return Supplier.create(**supplier_data)
    
    def get(self, supplier_id: int) -> Optional[Supplier]:
        """Get supplier by ID."""
        try:
            return Supplier.get_by_id(supplier_id)
        except Supplier.DoesNotExist:
            return None
    
    def update(self, supplier_id: int, update_data: dict) -> Optional[Supplier]:
        """Update supplier with new data."""
        try:
            supplier = Supplier.get_by_id(supplier_id)
            for key, value in update_data.items():
                setattr(supplier, key, value)
            supplier.save()
            return supplier
        except Supplier.DoesNotExist:
            return None
    
    def delete(self, supplier_id: int) -> bool:
        """Delete supplier by ID."""
        try:
            supplier = Supplier.get_by_id(supplier_id)
            supplier.delete_instance()
            return True
        except Supplier.DoesNotExist:
            return False
    
    def list_all(self, branch_id: Optional[int] = None) -> List[Supplier]:
        """Get all suppliers, optionally filtered by branch."""
        query = Supplier.select()
        if branch_id:
            query = query.where(Supplier.branch == branch_id)
        return list(query)
    
    def search(self, search_term: str) -> List[Supplier]:
        """Search suppliers by name, contact person, email, or phone."""
        search_term = search_term.lower()
        return list(Supplier.select().where(
            (fn.LOWER(Supplier.name).contains(search_term)) |
            (fn.LOWER(Supplier.contact_person).contains(search_term)) |
            (fn.LOWER(Supplier.email).contains(search_term)) |
            (fn.LOWER(Supplier.phone).contains(search_term))
        ))