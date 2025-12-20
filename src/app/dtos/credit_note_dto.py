"""CreditNote DTO - Data Transfer Object."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class CreditNoteDTO:
    """Data Transfer Object for CreditNote."""
    
    id: Optional[int] = None
    credit_note_number: str = ""
    purchase_return_id: Optional[int] = None
    supplier_invoice_id: Optional[int] = None
    credit_amount: Decimal = Decimal("0.00")
    applied_amount: Decimal = Decimal("0.00")
    remaining_credit: Decimal = Decimal("0.00")
    status: str = "pending"
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None
    
    # Flattened
    supplier_name: Optional[str] = None
    return_number: Optional[str] = None
    invoice_number: Optional[str] = None
    is_expired: bool = False

    @classmethod
    def from_model(cls, cn) -> 'CreditNoteDTO':
        """Convert model to DTO."""
        dto = cls(
            id=cn.id,
            credit_note_number=cn.credit_note_number,
            purchase_return_id=cn.purchase_return_id if cn.purchase_return else None,
            supplier_invoice_id=cn.supplier_invoice_id if cn.supplier_invoice else None,
            credit_amount=cn.credit_amount,
            applied_amount=cn.applied_amount,
            remaining_credit=cn.remaining_credit,
            status=cn.status,
            issue_date=cn.issue_date,
            expiry_date=cn.expiry_date,
            notes=cn.notes,
            supplier_name=cn.supplier.name if cn.supplier else None,
            return_number=cn.purchase_return.return_number if cn.purchase_return else None,
            invoice_number=cn.supplier_invoice.invoice_number if cn.supplier_invoice else None,
            is_expired=cn.is_expired
        )
        return dto
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'credit_note_id': self.id,
            'credit_note_number': self.credit_note_number,
            'purchase_return_id': self.purchase_return_id,
            'supplier_invoice_id': self.supplier_invoice_id,
            'credit_amount': float(self.credit_amount),
            'applied_amount': float(self.applied_amount),
            'remaining_credit': float(self.remaining_credit),
            'status': self.status,
            'notes': self.notes,
            'issue_date': self.issue_date.isoformat() if hasattr(self.issue_date, 'isoformat') else self.issue_date,
            'expiry_date': self.expiry_date.isoformat() if hasattr(self.expiry_date, 'isoformat') else self.expiry_date
        }
