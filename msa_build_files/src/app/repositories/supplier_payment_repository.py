"""SupplierPayment Repository - Supplier Payment Data Access Layer.

This repository handles all database operations for SupplierPayment entities.
Features include payment tracking and calculation of totals.
"""

from typing import List, Optional
from models.supplier_payment import SupplierPayment
from peewee import DoesNotExist, fn


class SupplierPaymentRepository:
    """Repository for SupplierPayment data access operations."""
    
    def create(self, payment_data: dict) -> SupplierPayment:
        """Create a new payment."""
        return SupplierPayment.create(**payment_data)
    
    def get(self, payment_id: int) -> Optional[SupplierPayment]:
        """Get payment by ID."""
        try:
            return SupplierPayment.get_by_id(payment_id)
        except DoesNotExist:
            return None
    
    def update(self, payment_id: int, update_data: dict) -> Optional[SupplierPayment]:
        """Update a payment."""
        try:
            payment = SupplierPayment.get_by_id(payment_id)
            for key, value in update_data.items():
                setattr(payment, key, value)
            payment.save()
            return payment
        except DoesNotExist:
            return None
    
    def delete(self, payment_id: int) -> bool:
        """Delete a payment."""
        try:
            payment = SupplierPayment.get_by_id(payment_id)
            payment.delete_instance()
            return True
        except DoesNotExist:
            return False
    
    def get_by_invoice(self, invoice_id: int) -> List[SupplierPayment]:
        """Get all payments for a specific invoice."""
        return list(
            SupplierPayment.select()
            .where(SupplierPayment.invoice == invoice_id)
            .order_by(SupplierPayment.payment_date.desc())
        )
    
    def get_by_supplier(self, supplier_id: int) -> List[SupplierPayment]:
        """Get all payments for a specific supplier via invoice chain."""
        from models.supplier_invoice import SupplierInvoice
        from models.purchase_order import PurchaseOrder
        return list(
            SupplierPayment.select()
            .join(SupplierInvoice)
            .join(PurchaseOrder)
            .where(PurchaseOrder.supplier == supplier_id)
            .order_by(SupplierPayment.payment_date.desc())
        )
    
    def calculate_total_paid(self, invoice_id: int) -> float:
        """Calculate total amount paid for an invoice."""
        result = (SupplierPayment.select(fn.SUM(SupplierPayment.amount))
                 .where(SupplierPayment.invoice == invoice_id)
                 .scalar())
        return float(result) if result else 0.0
    
    def get_all(self) -> List[SupplierPayment]:
        """Get all payments."""
        return list(SupplierPayment.select().order_by(SupplierPayment.payment_date.desc()))
