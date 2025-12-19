"""SupplierInvoice Repository - Supplier Invoice Data Access Layer.

This repository handles all database operations for SupplierInvoice entities.
Features include invoice creation, tracking outstanding balances, and payment status.
"""

from typing import List, Optional
from models.supplier_invoice import SupplierInvoice
from peewee import DoesNotExist


class SupplierInvoiceRepository:
    """Repository for SupplierInvoice data access operations."""
    
    def create(self, invoice_data: dict) -> SupplierInvoice:
        """Create a new supplier invoice."""
        return SupplierInvoice.create(**invoice_data)
    
    def get(self, invoice_id: int) -> Optional[SupplierInvoice]:
        """Get invoice by ID."""
        try:
            return SupplierInvoice.get_by_id(invoice_id)
        except DoesNotExist:
            return None
    
    def get_by_invoice_number(self, invoice_number: str) -> Optional[SupplierInvoice]:
        """Get invoice by invoice number."""
        try:
            return SupplierInvoice.get(SupplierInvoice.invoice_number == invoice_number)
        except DoesNotExist:
            return None
    
    def update(self, invoice_id: int, update_data: dict) -> Optional[SupplierInvoice]:
        """Update an invoice."""
        try:
            invoice = SupplierInvoice.get_by_id(invoice_id)
            for key, value in update_data.items():
                setattr(invoice, key, value)
            invoice.save()
            return invoice
        except DoesNotExist:
            return None
    
    def delete(self, invoice_id: int) -> bool:
        """Delete an invoice."""
        try:
            invoice = SupplierInvoice.get_by_id(invoice_id)
            invoice.delete_instance()
            return True
        except DoesNotExist:
            return False
    
    def get_by_supplier(self, supplier_id: int) -> List[SupplierInvoice]:
        """Get all invoices for a supplier via PurchaseOrder."""
        from models.purchase_order import PurchaseOrder
        return list(
            SupplierInvoice.select()
            .join(PurchaseOrder)
            .where(PurchaseOrder.supplier == supplier_id)
            .order_by(SupplierInvoice.invoice_date.desc())
        )
    
    def get_by_po(self, po_id: int) -> List[SupplierInvoice]:
        """Get all invoices for a purchase order."""
        return list(
            SupplierInvoice.select()
            .where(SupplierInvoice.purchase_order == po_id)
            .order_by(SupplierInvoice.invoice_date.desc())
        )
    
    def get_outstanding(self, supplier_id: Optional[int] = None) -> List[SupplierInvoice]:
        """Get all outstanding invoices (not fully paid)."""
        from models.purchase_order import PurchaseOrder
        query = SupplierInvoice.select().where(
            SupplierInvoice.status.in_(['pending', 'partial', 'overdue'])
        )
        
        if supplier_id:
            query = query.join(PurchaseOrder).where(
                PurchaseOrder.supplier == supplier_id
            )
        
        return list(query.order_by(SupplierInvoice.due_date))
    
    def get_overdue(self, supplier_id: Optional[int] = None) -> List[SupplierInvoice]:
        """Get all overdue invoices."""
        from models.purchase_order import PurchaseOrder
        query = SupplierInvoice.select().where(
            SupplierInvoice.status == 'overdue'
        )
        
        if supplier_id:
            query = query.join(PurchaseOrder).where(
                PurchaseOrder.supplier == supplier_id
            )
        
        return list(query.order_by(SupplierInvoice.due_date))
    
    def calculate_outstanding_balance(self, supplier_id: int) -> float:
        """Calculate total outstanding balance for a supplier."""
        invoices = self.get_outstanding(supplier_id)
        return sum(invoice.outstanding_amount for invoice in invoices)
    
    def get_all(self) -> List[SupplierInvoice]:
        """Get all invoices."""
        return list(SupplierInvoice.select().order_by(SupplierInvoice.invoice_date.desc()))
