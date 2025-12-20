"""Warranty DTO - Data Transfer Object."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WarrantyDTO:
    """Data Transfer Object for Warranty."""
    
    id: Optional[int] = None
    type: str = ""
    terms: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str = "active"
    warrantyable_type: str = "device"
    warrantyable_id: int = 0
    supplier_id: Optional[int] = None
    
    # Flattened
    supplier_name: Optional[str] = None
    
    # Computed
    is_active: bool = False
    days_remaining: int = 0

    @classmethod
    def from_model(cls, warranty) -> 'WarrantyDTO':
        """Convert model to DTO."""
        now = datetime.now()
        is_active = False
        days_remaining = 0
        
        if warranty.status == 'active' and warranty.end_date:
            if warranty.end_date > now:
                is_active = True
                delta = warranty.end_date - now
                days_remaining = delta.days
            else:
                is_active = False
        
        dto = cls(
            id=warranty.id,
            type=warranty.type,
            terms=warranty.terms,
            start_date=warranty.start_date,
            end_date=warranty.end_date,
            status=warranty.status,
            warrantyable_type=warranty.warrantyable_type,
            warrantyable_id=warranty.warrantyable_id,
            supplier_id=warranty.supplier_id if warranty.supplier else None,
            supplier_name=warranty.supplier.name if warranty.supplier else None,
            is_active=is_active,
            days_remaining=days_remaining
        )
        return dto
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'warranty_id': self.id,
            'type': self.type,
            'terms': self.terms,
            'status': self.status,
            'warrantyable_type': self.warrantyable_type,
            'warrantyable_id': self.warrantyable_id,
            'supplier_id': self.supplier_id,
            'start_date': self.start_date.isoformat() if hasattr(self.start_date, 'isoformat') else self.start_date,
            'end_date': self.end_date.isoformat() if hasattr(self.end_date, 'isoformat') else self.end_date
        }
