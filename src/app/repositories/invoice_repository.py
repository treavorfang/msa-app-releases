"""Invoice Repository - Invoice Data Access Layer.

This repository handles all database operations for Invoice entities.
Features include invoice creation, updating, deletion, filtering, and search.
"""

from typing import Optional, List
from peewee import fn
from models.invoice import Invoice
from models.device import Device
from models.customer import Customer


from models.payment import Payment
from peewee import prefetch

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
    
    def list_all(self, limit: int = 20, offset: int = 0, search: Optional[str] = None, customer_id: Optional[int] = None) -> List[Invoice]:
        """Get all invoices with pagination and filters."""
        query = Invoice.select().order_by(Invoice.created_at.desc())
        
        if customer_id:
            # Join through Device -> Customer
            query = query.join(Device).join(Customer).where(Customer.id == customer_id)
            
        if search:
            # Search by number or customer name
            query = query.join(Device).join(Customer).where(
                (Invoice.invoice_number.contains(search)) | 
                (Customer.name.contains(search))
            )
            
        # Execute query with limit/offset and prefetch payments
        final_query = query.limit(limit).offset(offset)
        return list(prefetch(final_query, Payment))
    
    def list_for_customer(self, customer_id: int) -> List[Invoice]:
        """Get all invoices for a specific customer."""
        return list(Invoice.select().join(Device).where(Device.customer == customer_id))

    def search(self, search_term: str) -> List[Invoice]:
        """Search invoices by invoice number."""
        search_term = search_term.lower()
        return list(Invoice.select().where(
            (fn.LOWER(Invoice.invoice_number).contains(search_term))
        ))