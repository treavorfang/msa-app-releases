"""RepairPart DTO - Data Transfer Object for Repair Parts."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class RepairPartDTO:
    """Data Transfer Object for RepairPart."""
    
    id: Optional[int] = None
    ticket_id: Optional[int] = None
    part_id: Optional[int] = None
    technician_id: Optional[int] = None
    quantity: int = 1
    installed_at: Optional[datetime] = None
    warranty_terms: Optional[str] = None
    warranty_ends: Optional[datetime] = None
    
    # Flattened fields for UI
    part_name: Optional[str] = None
    part_sku: Optional[str] = None
    part_price: Optional[float] = None  # Current price might differ, but useful for display if no snapshot
    part_cost: Optional[float] = None
    technician_name: Optional[str] = None
    
    @classmethod
    def from_model(cls, repair_part) -> 'RepairPartDTO':
        """Convert RepairPart model to DTO."""
        dto = cls(
            id=repair_part.id,
            ticket_id=repair_part.ticket_id,
            part_id=repair_part.part_id if repair_part.part else None,
            technician_id=repair_part.technician_id if repair_part.technician else None,
            quantity=repair_part.quantity,
            installed_at=repair_part.installed_at,
            warranty_terms=repair_part.warranty_terms,
            warranty_ends=repair_part.warranty_ends
        )
        
        # Populate flattened fields
        if repair_part.part:
            dto.part_name = repair_part.part.name
            dto.part_sku = repair_part.part.sku
            # Accessing properties might be dangerous if Part model changes, assume attributes exist
            if hasattr(repair_part.part, 'sell_price'):
                dto.part_price = float(repair_part.part.sell_price)
            if hasattr(repair_part.part, 'cost_price'):
                dto.part_cost = float(repair_part.part.cost_price)
                
        if repair_part.technician and hasattr(repair_part.technician, 'user') and repair_part.technician.user:
            dto.technician_name = repair_part.technician.user.name
        elif repair_part.technician:
            dto.technician_name = f"Tech #{repair_part.technician.id}"
            
        return dto

    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'repair_part_id': self.id,
            'ticket_id': self.ticket_id,
            'part_id': self.part_id,
            'quantity': self.quantity,
            'part_name': self.part_name
        }
