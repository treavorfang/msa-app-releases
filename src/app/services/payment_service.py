"""PaymentService - Payment Processing Business Logic.

This service manages payment records using DTOs and ensures invoice statuses are updated.
"""

from typing import List, Optional, Any, Dict
from datetime import datetime
from interfaces.ipayment_service import IPaymentService
from repositories.payment_repository import PaymentRepository
from repositories.invoice_repository import InvoiceRepository
from services.audit_service import AuditService
from dtos.payment_dto import PaymentDTO
from models.payment import Payment


class PaymentService(IPaymentService):
    """Service class for Payment operations."""
    
    def __init__(self, audit_service: AuditService):
        """Initialize PaymentService."""
        self.repository = PaymentRepository()
        self.invoice_repository = InvoiceRepository()
        self.audit_service = audit_service
        
    def create_payment(self, payment_data: dict, current_user=None, ip_address=None) -> PaymentDTO:
        """Create a new payment record."""
        payment = self.repository.create(payment_data)
        
        # Update linked invoice status
        if payment.invoice:
            self._update_invoice_status(payment.invoice.id)
        
        dto = PaymentDTO.from_model(payment)
        
        self.audit_service.log_action(
            user=current_user,
            action="payment_create",
            table_name="payments",
            new_data=dto.to_audit_dict(),
            ip_address=ip_address
        )
        return dto
        
    def get_payment(self, payment_id: int) -> Optional[PaymentDTO]:
        """Get a payment by ID."""
        payment = self.repository.get(payment_id)
        return PaymentDTO.from_model(payment) if payment else None
        
    def update_payment(self, payment_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[PaymentDTO]:
        """Update an existing payment."""
        old_payment = self.repository.get(payment_id)
        if not old_payment:
            return None
            
        old_dto = PaymentDTO.from_model(old_payment)
        payment = self.repository.update(payment_id, update_data)
        
        if payment:
            # Update invoice status
            if payment.invoice:
                self._update_invoice_status(payment.invoice.id)
                
            new_dto = PaymentDTO.from_model(payment)
            self.audit_service.log_action(
                user=current_user,
                action="payment_update",
                table_name="payments",
                old_data=old_dto.to_audit_dict(),
                new_data=new_dto.to_audit_dict(),
                ip_address=ip_address
            )
            return new_dto
        return None
        
    def delete_payment(self, payment_id: int, current_user=None, ip_address=None) -> bool:
        """Delete a payment record."""
        payment = self.repository.get(payment_id)
        if not payment:
            return False
            
        dto = PaymentDTO.from_model(payment)
        invoice_id = payment.invoice.id if payment.invoice else None
        
        success = self.repository.delete(payment_id)
        
        if success:
            if invoice_id:
                self._update_invoice_status(invoice_id)
                
            self.audit_service.log_action(
                user=current_user,
                action="payment_delete",
                table_name="payments",
                old_data=dto.to_audit_dict(),
                ip_address=ip_address
            )
        return success
        
    def get_payments_for_invoice(self, invoice_id: int) -> List[PaymentDTO]:
        """Get all payments associated with an invoice."""
        payments = self.repository.get_for_invoice(invoice_id)
        return [PaymentDTO.from_model(p) for p in payments]
        
    def get_total_paid_for_invoice(self, invoice_id: int) -> float:
        """Calculate total amount paid for an invoice."""
        return float(self.repository.get_total_paid(invoice_id))
    
    def _update_invoice_status(self, invoice_id: int):
        """Internal helper to update invoice payment status."""
        invoice = self.invoice_repository.get(invoice_id)
        if not invoice:
            return
            
        paid_amount = float(self.repository.get_total_paid(invoice_id))
        total_amount = float(invoice.total) if invoice.total else 0.0
        
        status = 'unpaid'
        paid_date = invoice.paid_date
        
        if paid_amount >= total_amount:
            status = 'paid'
            if not paid_date:
                paid_date = datetime.now()
        elif paid_amount > 0:
            status = 'partially_paid'
            paid_date = None
        else:
            status = 'unpaid'
            paid_date = None
            
        self.invoice_repository.update(invoice_id, {
            'payment_status': status,
            'paid_date': paid_date
        })