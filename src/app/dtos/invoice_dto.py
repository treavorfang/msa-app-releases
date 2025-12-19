"""Invoice DTO - Data Transfer Object for Invoice."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from dtos.invoice_item_dto import InvoiceItemDTO
from dtos.payment_dto import PaymentDTO


@dataclass
class InvoiceDTO:
    """Data Transfer Object for Invoice entity."""
    
    id: Optional[int] = None
    invoice_number: str = ""
    subtotal: Decimal = Decimal("0.00")
    tax: Decimal = Decimal("0.00")
    discount: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")
    payment_status: str = "unpaid"
    due_date: Optional[datetime] = None
    paid_date: Optional[datetime] = None
    device_id: Optional[int] = None
    branch_id: Optional[int] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None
    error_description: Optional[str] = None
    
    # Flattened / Convenience fields
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    device_serial: Optional[str] = None
    device_brand: Optional[str] = None
    device_model: Optional[str] = None
    
    # Financials
    paid_amount: Decimal = Decimal("0.00")
    balance_due: Decimal = Decimal("0.00")
    
    # Nested items
    items: List[InvoiceItemDTO] = field(default_factory=list)
    payments: List[PaymentDTO] = field(default_factory=list)

    @classmethod
    def from_model(cls, invoice) -> 'InvoiceDTO':
        """Convert Invoice model to InvoiceDTO."""
        # Handle optional relationships safely
        customer_name = None
        customer_phone = None
        customer_email = None
        device_serial = None
        device_brand = None
        device_model = None
        
        if invoice.device:
            device_serial = invoice.device.serial_number
            device_brand = invoice.device.brand
            # Handle model if it's a field
            device_model = invoice.device.model
            
            if invoice.device.customer:
                customer_name = invoice.device.customer.name
                customer_phone = invoice.device.customer.phone
                customer_email = invoice.device.customer.email
        
        # Calculate paid amount & populate payments
        paid_amt = Decimal("0.00")
        payments_list = []
        if hasattr(invoice, 'payments'):
            for payment in invoice.payments:
                paid_amt += payment.amount
                payments_list.append(PaymentDTO.from_model(payment))
        
        # Helper to ensure decimal
        def to_dec(val):
            if val is None:
                return Decimal("0.00")
            if isinstance(val, Decimal):
                return val
            return Decimal(str(val))

        total_dec = to_dec(invoice.total)
        
        dto = cls(
            id=invoice.id,
            invoice_number=invoice.invoice_number,
            subtotal=to_dec(invoice.subtotal),
            tax=to_dec(invoice.tax),
            discount=to_dec(invoice.discount),
            total=total_dec,
            payment_status=invoice.payment_status,
            due_date=invoice.due_date,
            paid_date=invoice.paid_date,
            device_id=invoice.device_id if invoice.device else None,
            branch_id=invoice.branch_id if hasattr(invoice, 'branch_id') else None,
            created_at=invoice.created_at,
            created_by=invoice.created_by_id if invoice.created_by else None,
            error_description=invoice.error_description,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            device_serial=device_serial,
            device_brand=device_brand,
            device_model=device_model,
            paid_amount=paid_amt,
            balance_due=total_dec - paid_amt,
            payments=payments_list
        )
        
        # Populate items if accessed
        if hasattr(invoice, 'items'):
            dto.items = [InvoiceItemDTO.from_model(item) for item in invoice.items]
            
        return dto
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'invoice_id': self.id,
            'invoice_number': self.invoice_number,
            'total': float(self.total),
            'status': self.payment_status,
            'items_count': len(self.items)
        }
