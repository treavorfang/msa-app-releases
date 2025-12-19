# src/app/dtos/customer_dto.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class CustomerDTO:
    id: Optional[int] = None
    name: str = ""
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    preferred_contact_method: str = "phone"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    branch_id: Optional[int] = None  # Added for completeness
    customer_name: Optional[str] = None  # For UI display consistency
    
    @classmethod
    def from_model(cls, customer) -> 'CustomerDTO':
        """Convert Customer model to CustomerDTO"""
        return cls(
            id=customer.id,
            name=customer.name,
            phone=customer.phone,
            email=customer.email,
            address=customer.address,
            notes=customer.notes,
            preferred_contact_method=customer.preferred_contact_method or "phone",
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            deleted_at=customer.deleted_at,
            created_by=customer.created_by_id,
            updated_by=customer.updated_by_id,
            branch_id=customer.branch_id if hasattr(customer, 'branch_id') else None
        )
    
    def to_dict(self) -> dict:
        """Convert DTO to dictionary for service/repository use"""
        return {
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'notes': self.notes,
            'preferred_contact_method': self.preferred_contact_method,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'branch_id': self.branch_id
        }
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging"""
        return {
            'customer_id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'preferred_contact_method': self.preferred_contact_method
        }
    
    def to_ui_dict(self) -> dict:
        """Convert to dictionary for UI display (safe fields only)"""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'preferred_contact_method': self.preferred_contact_method
            # Excludes sensitive fields like created_by, deleted_at, etc.
        }