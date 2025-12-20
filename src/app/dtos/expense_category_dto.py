"""ExpenseCategoryDTO - Data Transfer Object for Expense Categories."""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ExpenseCategoryDTO:
    """Data Transfer Object for Expense Category."""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    is_income: bool = False
    color: str = "#3B82F6"
    is_active: bool = True
    
    @classmethod
    def from_model(cls, category) -> 'ExpenseCategoryDTO':
        """Convert ExpenseCategory model to DTO."""
        return cls(
            id=category.id,
            name=category.name,
            description=category.description,
            is_income=category.is_income,
            color=category.color,
            is_active=category.is_active
        )
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'category_id': self.id,
            'name': self.name,
            'description': self.description,
            'is_income': self.is_income,
            'color': self.color,
            'is_active': self.is_active
        }
