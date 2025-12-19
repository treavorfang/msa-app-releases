"""Payment Repository - Payment Data Access Layer.

This repository handles all database operations for Payment entities.
Features include payment recording, retrieval, and calculations.
"""

from typing import Optional, List
from decimal import Decimal
from peewee import fn
from models.payment import Payment


class PaymentRepository:
    """Repository for Payment data access operations."""
    
    def create(self, payment_data: dict) -> Payment:
        """Record a new payment."""
        return Payment.create(**payment_data)
    
    def get(self, payment_id: int) -> Optional[Payment]:
        """Get payment by ID."""
        try:
            return Payment.get_by_id(payment_id)
        except Payment.DoesNotExist:
            return None
    
    def update(self, payment_id: int, update_data: dict) -> Optional[Payment]:
        """Update payment details."""
        try:
            payment = Payment.get_by_id(payment_id)
            for key, value in update_data.items():
                setattr(payment, key, value)
            payment.save()
            return payment
        except Payment.DoesNotExist:
            return None
    
    def delete(self, payment_id: int) -> bool:
        """Delete payment by ID."""
        try:
            payment = Payment.get_by_id(payment_id)
            payment.delete_instance()
            return True
        except Payment.DoesNotExist:
            return False
    
    def get_for_invoice(self, invoice_id: int) -> List[Payment]:
        """Get all payments for a specific invoice."""
        return list(Payment.select().where(Payment.invoice == invoice_id))
    
    def get_total_paid(self, invoice_id: int) -> Decimal:
        """Calculate total amount paid for an invoice."""
        result = (Payment
                 .select(fn.SUM(Payment.amount))
                 .where(Payment.invoice == invoice_id)
                 .scalar())
        return result or Decimal('0.00')