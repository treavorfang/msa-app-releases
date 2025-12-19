"""SupplierPaymentController - Bridge between UI and SupplierPaymentService."""

from PySide6.QtCore import QObject, Signal
from typing import List, Optional
from dtos.supplier_payment_dto import SupplierPaymentDTO


class SupplierPaymentController(QObject):
    """Controller for Supplier Payment management."""
    
    # Signals
    payment_recorded = Signal(object) # DTO
    payment_updated = Signal(object) # DTO
    payment_deleted = Signal(int)    # ID
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.service = container.supplier_payment_service
        self.current_user = getattr(container, 'current_user', None)
        
    def record_payment(self, payment_data: dict) -> Optional[SupplierPaymentDTO]:
        """Record a new payment."""
        payment = self.service.record_payment(
            payment_data,
            current_user=self.current_user
        )
        if payment:
            self.payment_recorded.emit(payment)
        return payment
        
    def get_payment(self, payment_id: int) -> Optional[SupplierPaymentDTO]:
        """Get a payment by ID."""
        return self.service.get_payment(payment_id)
        
    def update_payment(self, payment_id: int, update_data: dict) -> Optional[SupplierPaymentDTO]:
        """Update a payment."""
        payment = self.service.update_payment(
            payment_id,
            update_data,
            current_user=self.current_user
        )
        if payment:
            self.payment_updated.emit(payment)
        return payment
        
    def delete_payment(self, payment_id: int) -> bool:
        """Delete a payment."""
        success = self.service.delete_payment(
            payment_id,
            current_user=self.current_user
        )
        if success:
            self.payment_deleted.emit(payment_id)
        return success
        
    def get_payments_by_invoice(self, invoice_id: int) -> List[SupplierPaymentDTO]:
        """Get payments for invoice."""
        return self.service.get_payments_by_invoice(invoice_id)
        
    def get_payments_by_supplier(self, supplier_id: int) -> List[SupplierPaymentDTO]:
        """Get payments for supplier."""
        return self.service.get_payments_by_supplier(supplier_id)
        
    def list_payments(self) -> List[SupplierPaymentDTO]:
        """List all payments."""
        return self.service.list_payments()
