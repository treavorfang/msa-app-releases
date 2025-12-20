"""Part DTO - Data Transfer Object for Part."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from datetime import datetime


@dataclass
class PartDTO:
    """Data Transfer Object for Part."""
    
    id: Optional[int] = None
    sku: str = ""
    name: str = ""
    brand: Optional[str] = None
    model_compatibility: Optional[str] = None
    category_id: Optional[int] = None
    cost_price: Decimal = Decimal("0.00")
    min_stock_level: int = 0
    current_stock: int = 0
    barcode: Optional[str] = None
    branch_id: Optional[int] = None
    supplier_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    
    # Flattened
    category_name: Optional[str] = None
    supplier_name: Optional[str] = None
    
    # Computed
    is_low_stock: bool = False

    @classmethod
    def from_model(cls, part) -> 'PartDTO':
        """Convert Part model to DTO."""
        return cls(
            id=part.id,
            sku=part.sku,
            name=part.name,
            brand=part.brand,
            model_compatibility=part.model_compatibility,
            category_id=part.category_id if part.category else None,
            cost_price=part.cost_price,
            min_stock_level=part.min_stock_level,
            current_stock=part.current_stock,
            barcode=part.barcode,
            branch_id=part.branch_id if part.branch else None,
            supplier_id=part.supplier_id if part.supplier else None,
            created_at=part.created_at,
            updated_at=part.updated_at,
            is_active=part.is_active,
            
            category_name=part.category.name if part.category else None,
            supplier_name=part.supplier.name if part.supplier else None,
            
            is_low_stock=part.current_stock <= part.min_stock_level
        )
    
    def to_dict(self) -> dict:
        """Convert DTO to dictionary for service usage."""
        return {
            'sku': self.sku,
            'name': self.name,
            'brand': self.brand,
            'model_compatibility': self.model_compatibility,
            'category': self.category_id,
            'cost_price': self.cost_price,
            'min_stock_level': self.min_stock_level,
            'current_stock': self.current_stock,
            'barcode': self.barcode,
            'branch': self.branch_id,
            'supplier': self.supplier_id,
            'is_active': self.is_active
        }
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'part_id': self.id,
            'sku': self.sku,
            'name': self.name,
            'brand': self.brand,
            'model_compatibility': self.model_compatibility,
            'category_id': self.category_id,
            'supplier_id': self.supplier_id,
            'branch_id': self.branch_id,
            'cost_price': float(self.cost_price),
            'current_stock': self.current_stock,
            'min_stock_level': self.min_stock_level,
            'barcode': self.barcode,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else self.created_at,
            'updated_at': self.updated_at.isoformat() if hasattr(self.updated_at, 'isoformat') else self.updated_at
        }
