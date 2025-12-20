"""Category DTO - Data Transfer Object for Categories."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class CategoryDTO:
    """Data Transfer Object for Category."""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    parent_id: Optional[int] = None
    default_markup_percentage: float = 0.0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    deleted_by_id: Optional[int] = None
    
    # Flattened / Related Fields
    parent_name: Optional[str] = None
    path: Optional[str] = None
    deleted_by_name: Optional[str] = None
    
    @classmethod
    def from_model(cls, category) -> 'CategoryDTO':
        """Convert Category model to DTO."""
        return cls(
            id=category.id,
            name=category.name,
            description=category.description,
            parent_id=category.parent_id if category.parent else None,
            default_markup_percentage=float(category.default_markup_percentage) if category.default_markup_percentage else 0.0,
            is_active=category.is_active,
            created_at=category.created_at,
            updated_at=category.updated_at,
            deleted_at=category.deleted_at,
            deleted_by_id=category.deleted_by.id if category.deleted_by else None,
            
            # Flattened
            parent_name=category.parent.name if category.parent else None,
            path=category.get_full_path() if hasattr(category, 'get_full_path') else category.name,
            deleted_by_name=category.deleted_by.username if category.deleted_by else None
        )
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'category_id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id,
            'default_markup_percentage': self.default_markup_percentage,
            'is_active': self.is_active,
            'deleted_by_id': self.deleted_by_id,
            'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else self.created_at,
            'updated_at': self.updated_at.isoformat() if hasattr(self.updated_at, 'isoformat') else self.updated_at,
            'deleted_at': self.deleted_at.isoformat() if hasattr(self.deleted_at, 'isoformat') else self.deleted_at
        }
