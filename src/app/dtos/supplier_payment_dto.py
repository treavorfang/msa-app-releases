"""SupplierPayment DTO - Data Transfer Object."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class SupplierPaymentDTO:
    """Data Transfer Object for SupplierPayment."""
    
    id: Optional[int] = None
    invoice_id: Optional[int] = None
    payment_date: Optional[datetime] = None
    amount: Decimal = Decimal("0.00")
    payment_method: str = "bank_transfer"
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    # Flattened
    invoice_number: Optional[str] = None
    supplier_name: Optional[str] = None

    @classmethod
    def from_model(cls, pay) -> 'SupplierPaymentDTO':
        """Convert model to DTO."""
        supplier_name = None
        if pay.invoice and pay.invoice.purchase_order and pay.invoice.purchase_order.supplier:
            supplier_name = pay.invoice.purchase_order.supplier.name
            
        dto = cls(
            id=pay.id,
            invoice_id=pay.invoice_id if pay.invoice else None,
            payment_date=pay.payment_date,
            amount=pay.amount,
            payment_method=pay.payment_method,
            reference_number=pay.reference_number,
            notes=pay.notes,
            created_at=pay.created_at,
            created_by=pay.created_by_id if pay.created_by else None,
            invoice_number=pay.invoice.invoice_number if pay.invoice else None,
            supplier_name=supplier_name
        )
        return dto
    
    def to_dict(self) -> dict:
        """Convert to dict."""
        return {
            'invoice_id': self.invoice_id,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'reference_number': self.reference_number,
            'notes': self.notes
        }

    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'payment_id': self.id,
            'invoice_id': self.invoice_id,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'reference_number': self.reference_number,
            'notes': self.notes,
            'created_by': self.created_by,
            'payment_date': self.payment_date.isoformat() if hasattr(self.payment_date, 'isoformat') else self.payment_date,
            'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else self.created_at
        }
