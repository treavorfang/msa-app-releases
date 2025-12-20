"""PurchaseReturn DTO - Data Transfer Object."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from dtos.purchase_return_item_dto import PurchaseReturnItemDTO


@dataclass
class PurchaseReturnDTO:
    """Data Transfer Object for PurchaseReturn."""
    
    id: Optional[int] = None
    return_number: str = ""
    purchase_order_id: Optional[int] = None
    return_date: Optional[datetime] = None
    reason: str = ""
    status: str = "draft"
    total_amount: Decimal = Decimal("0.00")
    notes: Optional[str] = None
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    # Flattened
    supplier_name: Optional[str] = None
    
    # Nested
    items: List[PurchaseReturnItemDTO] = field(default_factory=list)

    @classmethod
    def from_model(cls, pr) -> 'PurchaseReturnDTO':
        """Convert model to DTO."""
        supplier_name = None
        if pr.purchase_order and pr.purchase_order.supplier:
            supplier_name = pr.purchase_order.supplier.name
            
        dto = cls(
            id=pr.id,
            return_number=pr.return_number,
            purchase_order_id=pr.purchase_order_id if pr.purchase_order else None,
            return_date=pr.return_date,
            reason=pr.reason,
            status=pr.status,
            total_amount=pr.total_amount,
            notes=pr.notes,
            created_by=pr.created_by_id if pr.created_by else None,
            approved_by=pr.approved_by_id if pr.approved_by else None,
            approved_at=pr.approved_at,
            created_at=pr.created_at,
            supplier_name=supplier_name
        )
        
        if hasattr(pr, 'items'):
            dto.items = [PurchaseReturnItemDTO.from_model(item) for item in pr.items]
            
        return dto
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'return_id': self.id,
            'return_number': self.return_number,
            'purchase_order_id': self.purchase_order_id,
            'reason': self.reason,
            'status': self.status,
            'total_amount': float(self.total_amount),
            'notes': self.notes,
            'created_by': self.created_by,
            'approved_by': self.approved_by,
            'items_count': len(self.items),
            'return_date': self.return_date.isoformat() if hasattr(self.return_date, 'isoformat') else self.return_date,
            'approved_at': self.approved_at.isoformat() if hasattr(self.approved_at, 'isoformat') else self.approved_at,
            'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else self.created_at
        }
