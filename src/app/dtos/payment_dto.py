"""Payment DTO - Data Transfer Object."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class PaymentDTO:
    """Data Transfer Object for Payment."""
    
    id: Optional[int] = None
    invoice_id: Optional[int] = None
    amount: Decimal = Decimal("0.00")
    payment_method: str = "cash"
    transaction_id: Optional[str] = None
    notes: Optional[str] = None
    paid_at: Optional[datetime] = None
    received_by: Optional[int] = None
    
    # Flattened
    invoice_number: Optional[str] = None
    received_by_name: Optional[str] = None

    @classmethod
    def from_model(cls, payment) -> 'PaymentDTO':
        """Convert model to DTO."""
        dto = cls(
            id=payment.id,
            invoice_id=payment.invoice_id if payment.invoice else None,
            amount=payment.amount,
            payment_method=payment.payment_method,
            transaction_id=payment.transaction_id,
            notes=payment.notes,
            paid_at=payment.paid_at,
            received_by=payment.received_by_id if payment.received_by else None,
            invoice_number=payment.invoice.invoice_number if payment.invoice else None,
            received_by_name=payment.received_by.username if payment.received_by else None
        )
        return dto
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'payment_id': self.id,
            'invoice_id': self.invoice_id,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_id,
            'notes': self.notes,
            'received_by': self.received_by,
            'paid_at': self.paid_at.isoformat() if hasattr(self.paid_at, 'isoformat') else self.paid_at
        }
