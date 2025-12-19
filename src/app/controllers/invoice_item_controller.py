# src/app/controllers/invoice_item_controller.py
from PySide6.QtCore import QObject, Signal
from models.invoice_item import InvoiceItem
from typing import Optional

class InvoiceItemController(QObject):
    item_updated = Signal(InvoiceItem)
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.invoice_item_service = container.invoice_item_service
        
    def get_invoice_item(self, item_id: int) -> Optional[InvoiceItem]:
        return self.invoice_item_service.get_invoice_item(item_id)
        
    def update_invoice_item(self, item_id: int, update_data: dict) -> Optional[InvoiceItem]:
        item = self.invoice_item_service.update_invoice_item(item_id, update_data)
        if item:
            self.item_updated.emit(item)
        return item