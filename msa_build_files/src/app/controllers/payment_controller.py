"""PaymentController - Bridge between UI and PaymentService."""

from PySide6.QtCore import QObject, Signal
from typing import List, Optional
from dtos.payment_dto import PaymentDTO
from core.event_bus import EventBus
from core.events import (
    PaymentCreatedEvent, PaymentUpdatedEvent, PaymentDeletedEvent
)

class PaymentController(QObject):
    """Controller for Payment management."""
    
    # Signals now emit DTOs
    payment_created = Signal(object)
    payment_updated = Signal(object)
    payment_deleted = Signal(int)
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.payment_service = container.payment_service
        self.current_user = getattr(container, 'current_user', None)
        
    def create_payment(self, payment_data: dict, current_user=None, ip_address=None) -> Optional[PaymentDTO]:
        """Create a new payment."""
        user = current_user or self.current_user
        payment = self.payment_service.create_payment(
            payment_data, 
            current_user=user,
            ip_address=ip_address
        )
        if payment:
            self.payment_created.emit(payment)
            user_id = user.id if user else None
            EventBus.publish(PaymentCreatedEvent(payment.id, user_id))
        return payment
        
    def get_payment(self, payment_id: int) -> Optional[PaymentDTO]:
        """Get a payment by ID."""
        return self.payment_service.get_payment(payment_id)
        
    def update_payment(self, payment_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[PaymentDTO]:
        """Update a payment."""
        user = current_user or self.current_user
        payment = self.payment_service.update_payment(
            payment_id, 
            update_data, 
            current_user=user,
            ip_address=ip_address
        )
        if payment:
            self.payment_updated.emit(payment)
            user_id = user.id if user else None
            EventBus.publish(PaymentUpdatedEvent(payment.id, user_id))
        return payment
        
    def delete_payment(self, payment_id: int, current_user=None, ip_address=None) -> bool:
        """Delete a payment."""
        user = current_user or self.current_user
        success = self.payment_service.delete_payment(
            payment_id, 
            current_user=user,
            ip_address=ip_address
        )
        if success:
            self.payment_deleted.emit(payment_id)
            user_id = user.id if user else None
            EventBus.publish(PaymentDeletedEvent(payment_id, user_id))
        return success
        
    def get_payments_for_invoice(self, invoice_id: int) -> List[PaymentDTO]:
        """Get payments for an invoice."""
        return self.payment_service.get_payments_for_invoice(invoice_id)
        
    def get_total_paid_for_invoice(self, invoice_id: int) -> float:
        """Get total paid amount."""
        return self.payment_service.get_total_paid_for_invoice(invoice_id)