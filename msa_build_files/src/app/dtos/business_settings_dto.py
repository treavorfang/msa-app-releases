"""BusinessSettings DTO - Data Transfer Object."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class BusinessSettingsDTO:
    """Data Transfer Object for BusinessSettings."""
    
    business_name: str = ""
    business_phone: str = ""
    address: str = ""
    tax_id: Optional[str] = None
    logo_url: Optional[str] = None
    notes: str = ""
    default_tax_rate: Decimal = Decimal("0.00")

    @classmethod
    def from_model(cls, settings) -> 'BusinessSettingsDTO':
        """Convert model to DTO."""
        dto = cls(
            business_name=settings.business_name,
            business_phone=settings.business_phone,
            address=settings.address,
            tax_id=settings.tax_id,
            logo_url=settings.logo_url,
            notes=settings.notes,
            default_tax_rate=settings.default_tax_rate
        )
        return dto
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'business_name': self.business_name,
            'phone': self.business_phone,
            'address': self.address,
            'tax_id': self.tax_id,
            'tax_rate': float(self.default_tax_rate)
        }
