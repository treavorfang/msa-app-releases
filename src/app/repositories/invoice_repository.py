"""Invoice Repository - Invoice Data Access Layer.

This repository handles all database operations for Invoice entities.
Features include invoice creation, updating, deletion, filtering, and search.
"""

from typing import Optional, List
from peewee import fn
from models.invoice import Invoice
from models.device import Device


class InvoiceRepository:
    """Repository for Invoice data access operations."""
    
    def create(self, invoice_data: dict) -> Invoice:
        """Create a new invoice."""
        return Invoice.create(**invoice_data)
    
    def get(self, invoice_id: int) -> Optional[Invoice]:
        """Get invoice by ID."""
        try:
            return Invoice.get_by_id(invoice_id)
        except Invoice.DoesNotExist:
            return None
    
    def update(self, invoice_id: int, update_data: dict) -> Optional[Invoice]:
        """Update invoice with new data."""
        try:
            invoice = Invoice.get_by_id(invoice_id)
            for key, value in update_data.items():
                setattr(invoice, key, value)
            invoice.save()
            return invoice
        except Invoice.DoesNotExist:
            return None
    
    def delete(self, invoice_id: int) -> bool:
        """Delete invoice by ID."""
        try:
            invoice = Invoice.get_by_id(invoice_id)
            invoice.delete_instance()
            return True
        except Invoice.DoesNotExist:
            return False
    
    def list_all(self, branch_id: Optional[int] = None) -> List[Invoice]:
        """Get all invoices, optionally filtered by branch."""
        query = Invoice.select()
        if branch_id:
            query = query.where(Invoice.branch == branch_id)
        return list(query)
    
    def list_for_customer(self, customer_id: int) -> List[Invoice]:
        """Get all invoices for a specific customer."""
        return list(Invoice.select().join(Device).where(Device.customer == customer_id))

    def search(self, search_term: str) -> List[Invoice]:
        """Search invoices by invoice number."""
        search_term = search_term.lower()
        return list(Invoice.select().where(
            (fn.LOWER(Invoice.invoice_number).contains(search_term))
        ))