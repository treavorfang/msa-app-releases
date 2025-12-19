"""PurchaseOrderItem DTO - Data Transfer Object for Purchase Order Item."""

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal


@dataclass
class PurchaseOrderItemDTO:
    """Data Transfer Object for PurchaseOrderItem."""
    
    id: Optional[int] = None
    purchase_order_id: Optional[int] = None
    part_id: Optional[int] = None
    quantity: int = 1
    unit_cost: Decimal = Decimal("0.00")
    total_cost: Decimal = Decimal("0.00")
    received_quantity: int = 0
    
    # Flattened
    part_name: Optional[str] = None
    part_sku: Optional[str] = None

    @classmethod
    def from_model(cls, item) -> 'PurchaseOrderItemDTO':
        """Convert PurchaseOrderItem model to DTO."""
        part_name = item.part.name if item.part else None
        part_sku = item.part.sku if item.part else None
        
        return cls(
            id=item.id,
            purchase_order_id=item.purchase_order_id,
            part_id=item.part_id,
            quantity=item.quantity,
            unit_cost=item.unit_cost,
            total_cost=item.total_cost,
            received_quantity=item.received_quantity,
            part_name=part_name,
            part_sku=part_sku
        )
