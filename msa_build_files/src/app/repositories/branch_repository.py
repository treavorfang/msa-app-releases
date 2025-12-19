"""Branch Repository - Branch Data Access Layer.

This repository handles all database operations for Branch entities.
Features include branch management and location search.
"""

from typing import Optional, List
from peewee import fn
from models.branch import Branch


class BranchRepository:
    """Repository for Branch data access operations."""
    
    def create(self, branch_data: dict) -> Branch:
        """Create a new branch."""
        return Branch.create(**branch_data)
    
    def get(self, branch_id: int) -> Optional[Branch]:
        """Get branch by ID."""
        try:
            return Branch.get_by_id(branch_id)
        except Branch.DoesNotExist:
            return None
    
    def update(self, branch_id: int, update_data: dict) -> Optional[Branch]:
        """Update branch with new data."""
        try:
            branch = Branch.get_by_id(branch_id)
            for key, value in update_data.items():
                setattr(branch, key, value)
            branch.save()
            return branch
        except Branch.DoesNotExist:
            return None
    
    def delete(self, branch_id: int) -> bool:
        """Delete branch by ID."""
        try:
            branch = Branch.get_by_id(branch_id)
            branch.delete_instance()
            return True
        except Branch.DoesNotExist:
            return False
    
    def list_all(self) -> List[Branch]:
        """Get all branches."""
        return list(Branch.select())
    
    def search(self, search_term: str) -> List[Branch]:
        """Search branches by name, address, or phone."""
        search_term = search_term.lower()
        return list(Branch.select().where(
            (fn.LOWER(Branch.name).contains(search_term)) |
            (fn.LOWER(Branch.address).contains(search_term)) |
            (fn.LOWER(Branch.phone).contains(search_term))
        ))