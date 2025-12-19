"""PurchaseReturnItem DTO - Data Transfer Object."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class PurchaseReturnItemDTO:
    """Data Transfer Object for PurchaseReturnItem."""
    
    id: Optional[int] = None
    purchase_return_id: Optional[int] = None
    part_id: Optional[int] = None
    quantity: int = 0
    unit_cost: Decimal = Decimal("0.00")
    total_cost: Decimal = Decimal("0.00")
    condition: str = "defective"
    notes: Optional[str] = None
    
    # Flattened
    part_name: Optional[str] = None
    part_sku: Optional[str] = None

    @classmethod
    def from_model(cls, item) -> 'PurchaseReturnItemDTO':
        """Convert model to DTO."""
        return cls(
            id=item.id,
            purchase_return_id=item.purchase_return_id,
            part_id=item.part_id,
            quantity=item.quantity,
            unit_cost=item.unit_cost,
            total_cost=item.total_cost,
            condition=item.condition,
            notes=item.notes,
            part_name=item.part.name if item.part else None,
            part_sku=item.part.sku if item.part else None
        )
