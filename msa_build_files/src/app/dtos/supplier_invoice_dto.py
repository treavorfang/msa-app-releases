"""SupplierInvoice DTO - Data Transfer Object."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class SupplierInvoiceDTO:
    """Data Transfer Object for SupplierInvoice."""
    
    id: Optional[int] = None
    purchase_order_id: Optional[int] = None
    invoice_number: str = ""
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    subtotal: Decimal = Decimal("0.00")
    discount: Decimal = Decimal("0.00")
    shipping_fee: Decimal = Decimal("0.00")
    total_amount: Decimal = Decimal("0.00")
    paid_amount: Decimal = Decimal("0.00")
    status: str = "pending"
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    # Flattened
    po_number: Optional[str] = None
    supplier_name: Optional[str] = None
    
    # Computed
    outstanding_amount: Decimal = Decimal("0.00")
    is_overdue: bool = False

    @classmethod
    def from_model(cls, inv) -> 'SupplierInvoiceDTO':
        """Convert model to DTO."""
        dto = cls(
            id=inv.id,
            purchase_order_id=inv.purchase_order_id if inv.purchase_order else None,
            invoice_number=inv.invoice_number,
            invoice_date=inv.invoice_date,
            due_date=inv.due_date,
            subtotal=inv.subtotal,
            discount=inv.discount,
            shipping_fee=inv.shipping_fee,
            total_amount=inv.total_amount,
            paid_amount=inv.paid_amount,
            status=inv.status,
            notes=inv.notes,
            created_at=inv.created_at,
            created_by=inv.created_by_id if inv.created_by else None,
            po_number=inv.purchase_order.po_number if inv.purchase_order else None,
            supplier_name=inv.purchase_order.supplier.name if inv.purchase_order and inv.purchase_order.supplier else None,
            outstanding_amount=Decimal(str(inv.outstanding_amount)),
            is_overdue=inv.is_overdue
        )
        return dto
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'invoice_id': self.id,
            'invoice_number': self.invoice_number,
            'total_amount': float(self.total_amount),
            'status': self.status
        }
