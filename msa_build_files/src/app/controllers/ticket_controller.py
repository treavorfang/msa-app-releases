# src/app/controllers/ticket_controller.py
from PySide6.QtCore import QObject, Signal
from dtos.ticket_dto import TicketDTO
# from views.tickets.ticket_receipt import TicketReceipt # Moved inside methods
from typing import Optional, List, TYPE_CHECKING
from core.event_bus import EventBus
from core.events import (
    TicketCreatedEvent, TicketUpdatedEvent, TicketDeletedEvent,
    TicketRestoredEvent, TicketStatusChangedEvent, TicketTechnicianAssignedEvent
)

if TYPE_CHECKING:
    from views.tickets.ticket_receipt import TicketReceipt

class TicketController(QObject):
    ticket_created = Signal(TicketDTO)
    ticket_updated = Signal(TicketDTO)
    ticket_deleted = Signal(int)
    ticket_restored = Signal(int)
    status_changed = Signal(TicketDTO)
    technician_assigned = Signal(TicketDTO)
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.ticket_service = container.ticket_service
        
    def create_ticket(self, ticket_data: dict, current_user=None, ip_address=None) -> Optional[TicketDTO]:
        ticket = self.ticket_service.create_ticket(ticket_data, current_user, ip_address)
        if ticket:
            self.ticket_created.emit(ticket)
            user_id = current_user.id if current_user else 0
            EventBus.publish(TicketCreatedEvent(ticket.id, user_id))
        return ticket
        
    def get_ticket(self, ticket_id: int, include_deleted: bool = False) -> Optional[TicketDTO]:
        return self.ticket_service.get_ticket(ticket_id, include_deleted)
        
    def update_ticket(self, ticket_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[TicketDTO]:
        ticket = self.ticket_service.update_ticket(ticket_id, update_data, current_user, ip_address)
        if ticket:
            self.ticket_updated.emit(ticket)
            user_id = current_user.id if current_user else 0
            EventBus.publish(TicketUpdatedEvent(ticket.id, user_id))
        return ticket
        
    def delete_ticket(self, ticket_id: int, current_user=None, ip_address=None) -> bool:
        success = self.ticket_service.delete_ticket(ticket_id, current_user, ip_address)
        if success:
            self.ticket_deleted.emit(ticket_id)
            user_id = current_user.id if current_user else 0
            EventBus.publish(TicketDeletedEvent(ticket_id, user_id))
        return success
        
    def restore_ticket(self, ticket_id: int, current_user=None, ip_address=None) -> bool:
        success = self.ticket_service.restore_ticket(ticket_id, current_user, ip_address)
        if success:
            self.ticket_restored.emit(ticket_id)
            user_id = current_user.id if current_user else 0
            EventBus.publish(TicketRestoredEvent(ticket_id, user_id))
        return success
        
    def list_tickets(self, filters: dict = None) -> List[TicketDTO]:
        return self.ticket_service.list_tickets(filters)
        
    def search_tickets(self, search_term: str) -> List[TicketDTO]:
        return self.ticket_service.search_tickets(search_term)
        
    def change_ticket_status(self, ticket_id: int, new_status: str, reason: str = None, current_user=None, ip_address=None) -> Optional[TicketDTO]:
        # Get old status for event
        old_ticket = self.get_ticket(ticket_id)
        old_status = old_ticket.status if old_ticket else ""
        
        ticket = self.ticket_service.change_ticket_status(
            ticket_id=ticket_id,
            new_status=new_status,
            reason=reason,
            current_user=current_user,
            ip_address=ip_address
        )
        if ticket:
            self.status_changed.emit(ticket)
            
            # Publish event
            user_id = current_user.id if current_user else 0
            EventBus.publish(TicketStatusChangedEvent(ticket.id, new_status, old_status, user_id))
            
            # Emit device_updated signal to refresh device tab
            if ticket.device_id and hasattr(self.container, 'device_controller'):
                device = self.container.device_controller.get_device(ticket.device_id)
                if device:
                    self.container.device_controller.device_updated.emit(device)
        return ticket
        
    def assign_ticket(self, ticket_id: int, technician_id: int, reason: str = None, current_user=None, ip_address=None) -> Optional[TicketDTO]:
        ticket = self.ticket_service.assign_ticket(ticket_id, technician_id, reason, current_user, ip_address)
        if ticket:
            self.technician_assigned.emit(ticket)
            user_id = current_user.id if current_user else 0
            EventBus.publish(TicketTechnicianAssignedEvent(ticket.id, technician_id, user_id))
        return ticket

    def show_new_ticket_receipt(self, user_id, parent=None):
        from views.tickets.ticket_receipt import TicketReceipt
        ticket_receipt = TicketReceipt(user_id, self.container, parent)
        ticket_receipt.ticket_created.connect(self._on_ticket_created)
        ticket_receipt.show()
        return ticket_receipt

    def _on_ticket_created(self, ticket):
        self.ticket_created.emit(ticket)
        # Event already published in create_ticket if called via controller, 
        # but TicketReceipt might call service directly? 
        # TicketReceipt calls controller.create_ticket usually.
        # Let's check TicketReceipt. It calls self.controller.create_ticket.
        # So we don't need to publish here to avoid duplicates.
        self.container.customer_controller.data_changed.emit()

    def _on_ticket_updated(self, ticket):
        self.ticket_updated.emit(ticket)
        # Same here, TicketReceipt calls controller.update_ticket
        self.container.customer_controller.data_changed.emit()

    def show_edit_ticket_form(self, ticket_id: int, parent=None) -> Optional["TicketReceipt"]:
        """Open the ticket receipt form in edit mode for an existing ticket"""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return None
            
        from views.tickets.ticket_receipt import TicketReceipt
        ticket_receipt = TicketReceipt(ticket.created_by_id, self.container, parent=None)
        ticket_receipt.set_edit_mode(ticket)
        ticket_receipt.ticket_updated.connect(self._on_ticket_updated)
        ticket_receipt.show()
        return ticket_receipt