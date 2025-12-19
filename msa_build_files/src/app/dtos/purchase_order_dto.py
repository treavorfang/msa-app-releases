"""PurchaseOrder DTO - Data Transfer Object for Purchase Order."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from dtos.purchase_order_item_dto import PurchaseOrderItemDTO


@dataclass
class PurchaseOrderDTO:
    """Data Transfer Object for PurchaseOrder."""
    
    id: Optional[int] = None
    po_number: str = ""
    supplier_id: Optional[int] = None
    status: str = "draft"
    order_date: Optional[datetime] = None
    expected_delivery: Optional[datetime] = None
    received_date: Optional[datetime] = None
    total_amount: Decimal = Decimal("0.00")
    notes: Optional[str] = None
    branch_id: Optional[int] = None
    created_by: Optional[int] = None
    
    # Flattened
    supplier_name: Optional[str] = None
    supplier_contact: Optional[str] = None
    supplier_phone: Optional[str] = None
    supplier_address: Optional[str] = None
    
    # Nested
    items: List[PurchaseOrderItemDTO] = field(default_factory=list)

    @classmethod
    def from_model(cls, po) -> 'PurchaseOrderDTO':
        """Convert PurchaseOrder model to DTO."""
        dto = cls(
            id=po.id,
            po_number=po.po_number,
            supplier_id=po.supplier_id if po.supplier else None,
            status=po.status,
            order_date=po.order_date,
            expected_delivery=po.expected_delivery,
            received_date=po.received_date,
            total_amount=po.total_amount,
            notes=po.notes,
            branch_id=po.branch_id if po.branch else None,
            created_by=po.created_by_id if po.created_by else None,
            supplier_name=po.supplier.name if po.supplier else None,
            supplier_contact=po.supplier.contact_person if po.supplier and hasattr(po.supplier, 'contact_person') else None,
            supplier_phone=po.supplier.phone if po.supplier and hasattr(po.supplier, 'phone') else None,
            supplier_address=po.supplier.address if po.supplier and hasattr(po.supplier, 'address') else None
        )
        
        # Hydrate items if available
        if hasattr(po, 'items'):
            dto.items = [PurchaseOrderItemDTO.from_model(item) for item in po.items]
            
        return dto
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'po_id': self.id,
            'po_number': self.po_number,
            'status': self.status,
            'total_amount': float(self.total_amount),
            'supplier_id': self.supplier_id
        }
