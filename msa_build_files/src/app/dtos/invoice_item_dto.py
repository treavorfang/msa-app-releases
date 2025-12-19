"""InvoiceItem DTO - Data Transfer Object for Invoice Item."""

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal


@dataclass
class InvoiceItemDTO:
    """Data Transfer Object for InvoiceLineItem entity."""
    
    id: Optional[int] = None
    invoice_id: Optional[int] = None
    item_id: Optional[int] = None
    item_type: str = "part"  # 'part' or 'service'
    quantity: int = 1
    unit_price: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")

    item_name: Optional[str] = None
    
    @classmethod
    def from_model(cls, item) -> 'InvoiceItemDTO':
        """Convert InvoiceItem model to DTO."""
        name = f"Item #{item.item_id}"
        
        try:
            if item.item_type == 'part':
                from models.part import Part
                p = Part.get_or_none(Part.id == item.item_id)
                if p:
                    name = p.name
            elif item.item_type == 'service':
                # Assuming Service model exists or fallback
                # from models.service import Service
                # s = Service.get_or_none(Service.id == item.item_id)
                pass # TODO: Implement Service lookup
        except Exception:
            pass
            
        return cls(
            id=item.id,
            invoice_id=item.invoice_id,
            item_id=item.item_id,
            item_type=item.item_type,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total=item.total,
            item_name=name
        )
    
    def to_dict(self) -> dict:
        """Convert DTO to dictionary."""
        return {
            'item_id': self.item_id,
            'item_type': self.item_type,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total': float(self.total)
        }
