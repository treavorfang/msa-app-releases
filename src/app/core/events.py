# src/app/core/events.py
from dataclasses import dataclass
from core.event_bus import Event

@dataclass
class TicketCreatedEvent(Event):
    ticket_id: int
    user_id: int

@dataclass
class TicketUpdatedEvent(Event):
    ticket_id: int
    user_id: int

@dataclass
class TicketStatusChangedEvent(Event):
    ticket_id: int
    new_status: str
    old_status: str
    user_id: int

@dataclass
class TicketDeletedEvent(Event):
    ticket_id: int
    user_id: int

@dataclass
class TicketRestoredEvent(Event):
    ticket_id: int
    user_id: int

@dataclass
class TicketTechnicianAssignedEvent(Event):
    ticket_id: int
    technician_id: int
    user_id: int

# Invoice Events
@dataclass
class InvoiceCreatedEvent(Event):
    invoice_id: int
    user_id: int = None

@dataclass
class InvoiceUpdatedEvent(Event):
    invoice_id: int
    user_id: int = None

@dataclass
class InvoiceDeletedEvent(Event):
    invoice_id: int
    user_id: int = None

# Customer Events
@dataclass
class CustomerCreatedEvent(Event):
    customer_id: int
    user_id: int = None

@dataclass
class CustomerUpdatedEvent(Event):
    customer_id: int
    user_id: int = None

@dataclass
class CustomerDeletedEvent(Event):
    customer_id: int
    user_id: int = None

# Device Events
@dataclass
class DeviceCreatedEvent(Event):
    device_id: int
    user_id: int = None

@dataclass
class DeviceUpdatedEvent(Event):
    device_id: int
    user_id: int = None

@dataclass
class DeviceDeletedEvent(Event):
    device_id: int
    user_id: int = None

@dataclass
class DeviceRestoredEvent(Event):
    device_id: int
    user_id: int = None

# Payment Events
@dataclass
class PaymentCreatedEvent(Event):
    payment_id: int
    user_id: int = None

@dataclass
class PaymentUpdatedEvent(Event):
    payment_id: int
    user_id: int = None

@dataclass
class PaymentDeletedEvent(Event):
    payment_id: int
    user_id: int = None

@dataclass
class TechnicianCreatedEvent(Event):
    technician_id: int
    user_id: int = None

@dataclass
class TechnicianUpdatedEvent(Event):
    technician_id: int
    user_id: int = None

@dataclass
class TechnicianDeactivatedEvent(Event):
    technician_id: int
    user_id: int = None

@dataclass
class BranchContextChangedEvent(Event):
    branch_id: int  # None for 'All Branches'

@dataclass
class LanguageContextChangedEvent(Event):
    language_code: str
    pass
