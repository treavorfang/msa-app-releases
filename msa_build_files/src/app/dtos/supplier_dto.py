"""Supplier DTO - Data Transfer Object for Supplier."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SupplierDTO:
    """Data Transfer Object for Supplier entity."""
    
    id: Optional[int] = None
    name: str = ""
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    branch_id: Optional[int] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None

    @classmethod
    def from_model(cls, supplier) -> 'SupplierDTO':
        """Convert Supplier model to SupplierDTO."""
        return cls(
            id=supplier.id,
            name=supplier.name,
            contact_person=supplier.contact_person,
            email=supplier.email,
            phone=supplier.phone,
            address=supplier.address,
            tax_id=supplier.tax_id,
            payment_terms=supplier.payment_terms,
            notes=supplier.notes,
            branch_id=supplier.branch.id if supplier.branch else None,
            created_at=supplier.created_at,
            created_by=supplier.created_by.id if supplier.created_by else None
        )
    
    def to_dict(self) -> dict:
        """Convert DTO to dictionary for service/repository use."""
        return {
            'name': self.name,
            'contact_person': self.contact_person,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'tax_id': self.tax_id,
            'payment_terms': self.payment_terms,
            'notes': self.notes,
            'branch': self.branch_id,
            'created_by': self.created_by
        }
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'supplier_id': self.id,
            'name': self.name,
            'contact_person': self.contact_person,
            'email': self.email,
            'phone': self.phone,
            'tax_id': self.tax_id
        }
