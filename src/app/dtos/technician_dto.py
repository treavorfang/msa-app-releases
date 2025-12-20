"""Technician DTO - Data Transfer Object."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class TechnicianDTO:
    """Data Transfer Object for Technician."""
    
    id: Optional[int] = None
    full_name: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    specialization: Optional[str] = None
    certification: Optional[str] = None
    salary: Decimal = Decimal("0.00")
    commission_rate: Decimal = Decimal("0.00")
    is_active: bool = True
    joined_at: Optional[datetime] = None
    profile_photo: Optional[str] = None

    @classmethod
    def from_model(cls, tech) -> 'TechnicianDTO':
        """Convert model to DTO."""
        dto = cls(
            id=tech.id,
            full_name=tech.full_name,
            email=tech.email,
            phone=tech.phone,
            address=tech.address,
            specialization=tech.specialization,
            certification=tech.certification,
            salary=tech.salary,
            commission_rate=tech.commission_rate,
            is_active=tech.is_active,
            joined_at=tech.joined_at,
            profile_photo=tech.profile_photo
        )
        return dto
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'technician_id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'specialization': self.specialization,
            'certification': self.certification,
            'salary': float(self.salary),
            'commission_rate': float(self.commission_rate),
            'is_active': self.is_active,
            'joined_at': self.joined_at.isoformat() if hasattr(self.joined_at, 'isoformat') else self.joined_at
        }
