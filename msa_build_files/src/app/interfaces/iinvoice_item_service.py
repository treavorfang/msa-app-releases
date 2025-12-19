# src/app/interfaces/iinvoice_item_service.py
from abc import ABC, abstractmethod
from models.invoice_item import InvoiceItem
from typing import Optional

class IInvoiceItemService(ABC):
    @abstractmethod
    def get_invoice_item(self, item_id: int) -> Optional[InvoiceItem]:
        pass
        
    @abstractmethod
    def update_invoice_item(self, item_id: int, update_data: dict) -> Optional[InvoiceItem]:
        pass