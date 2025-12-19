"""SupplierPaymentService - Supplier Payment Processing Logic.

This service manages payments using DTOs.
"""

from typing import List, Optional, Any, Dict
from interfaces.isupplier_payment_service import ISupplierPaymentService
from models.supplier_payment import SupplierPayment
from repositories.supplier_payment_repository import SupplierPaymentRepository
from repositories.supplier_invoice_repository import SupplierInvoiceRepository
from services.audit_service import AuditService
from dtos.supplier_payment_dto import SupplierPaymentDTO
from core.event_bus import EventBus
from core.events import PaymentCreatedEvent, PaymentUpdatedEvent, PaymentDeletedEvent


class SupplierPaymentService(ISupplierPaymentService):
    """Service class for Supplier Payment operations."""
    
    def __init__(self, audit_service: AuditService):
        """Initialize SupplierPaymentService."""
        self._audit_service = audit_service
        self._repository = SupplierPaymentRepository()
        self._invoice_repository = SupplierInvoiceRepository()
    
    def record_payment(self, payment_data: dict, current_user=None, ip_address=None) -> SupplierPaymentDTO:
        """Record a new payment and update the related invoice."""
        payment = self._repository.create(payment_data)
        
        # Update invoice paid_amount
        invoice = self._invoice_repository.get(payment.invoice.id)
        if invoice:
            new_paid_amount = float(invoice.paid_amount) + float(payment.amount)
            self._invoice_repository.update(invoice.id, {'paid_amount': new_paid_amount})
        
        dto = SupplierPaymentDTO.from_model(payment)
        
        self._audit_service.log_action(
            user=current_user,
            action="create",
            table_name="supplier_payments",
            new_data=dto.to_audit_dict(),
            ip_address=ip_address
        )
        
        # Publish event
        EventBus.publish(PaymentCreatedEvent(payment_id=payment.id))
        
        return dto
    
    def get_payment(self, payment_id: int) -> Optional[SupplierPaymentDTO]:
        """Get a payment by ID."""
        pay = self._repository.get(payment_id)
        return SupplierPaymentDTO.from_model(pay) if pay else None
    
    def update_payment(self, payment_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[SupplierPaymentDTO]:
        """Update a payment and adjust the invoice balance."""
        old_payment = self._repository.get(payment_id)
        if not old_payment:
            return None
        
        old_dto = SupplierPaymentDTO.from_model(old_payment)
        
        # If amount is being changed, update invoice paid_amount
        if 'amount' in update_data:
            old_amount = float(old_payment.amount)
            new_amount = float(update_data['amount'])
            amount_diff = new_amount - old_amount
            
            invoice = self._invoice_repository.get(old_payment.invoice.id)
            if invoice:
                new_paid_amount = float(invoice.paid_amount) + amount_diff
                self._invoice_repository.update(invoice.id, {'paid_amount': new_paid_amount})
        
        payment = self._repository.update(payment_id, update_data)
        
        if payment:
            new_dto = SupplierPaymentDTO.from_model(payment)
            self._audit_service.log_action(
                user=current_user,
                action="update",
                table_name="supplier_payments",
                old_data=old_dto.to_audit_dict(),
                new_data=new_dto.to_audit_dict(),
                ip_address=ip_address
            )
            
            # Publish event
            EventBus.publish(PaymentUpdatedEvent(payment_id=payment_id))
            
            return new_dto
        return None
    
    def delete_payment(self, payment_id: int, current_user=None, ip_address=None) -> bool:
        """Delete a payment and reverse the invoice balance update."""
        payment = self._repository.get(payment_id)
        if not payment:
            return False
            
        dto = SupplierPaymentDTO.from_model(payment)
        
        # Update invoice paid_amount
        invoice = self._invoice_repository.get(payment.invoice.id)
        if invoice:
            new_paid_amount = float(invoice.paid_amount) - float(payment.amount)
            self._invoice_repository.update(invoice.id, {'paid_amount': new_paid_amount})
        
        success = self._repository.delete(payment_id)
        
        if success:
            self._audit_service.log_action(
                user=current_user,
                action="delete",
                table_name="supplier_payments",
                old_data=dto.to_audit_dict(),
                ip_address=ip_address
            )
            
            # Publish event
            EventBus.publish(PaymentDeletedEvent(payment_id=payment_id))
        
        return success
    
    def get_payments_by_invoice(self, invoice_id: int) -> List[SupplierPaymentDTO]:
        """Get all payments for a specific invoice."""
        payments = self._repository.get_by_invoice(invoice_id)
        return [SupplierPaymentDTO.from_model(p) for p in payments]
    
    def get_payments_by_supplier(self, supplier_id: int) -> List[SupplierPaymentDTO]:
        """Get all payments for a specific supplier."""
        payments = self._repository.get_by_supplier(supplier_id)
        return [SupplierPaymentDTO.from_model(p) for p in payments]
    
    def get_all_payments(self) -> List[SupplierPaymentDTO]:
        """Get all payments."""
        payments = self._repository.get_all()
        return [SupplierPaymentDTO.from_model(p) for p in payments]
    
    def list_payments(self) -> List[SupplierPaymentDTO]:
        """List all payments."""
        return self.get_all_payments()
