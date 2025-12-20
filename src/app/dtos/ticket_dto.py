# src/app/dtos/ticket_dto.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from dtos.device_dto import DeviceDTO
from dtos.customer_dto import CustomerDTO

@dataclass
class TicketDTO:
    id: Optional[int] = None
    ticket_number: str = ""
    device_id: Optional[int] = None
    created_by_id: Optional[int] = None
    branch_id: Optional[int] = None
    created_at: Optional[datetime] = None
    status: str = "open"
    priority: str = "medium"
    error: Optional[str] = None
    error_description: Optional[str] = None
    accessories: Optional[str] = None
    internal_notes: Optional[str] = None
    estimated_cost: float = 0.00
    actual_cost: float = 0.00
    deposit_paid: float = 0.00
    assigned_technician_id: Optional[int] = None
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    warranty_covered: bool = False
    approved_by_id: Optional[int] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    
    # Related objects (for UI display)
    device: Optional[DeviceDTO] = None
    customer: Optional[CustomerDTO] = None
    technician_name: Optional[str] = None
    created_by_name: Optional[str] = None
    
    @classmethod
    def from_model(cls, ticket) -> 'TicketDTO':
        """Convert Ticket model to TicketDTO"""
        return cls(
            id=ticket.id,
            ticket_number=ticket.ticket_number,
            device_id=ticket.device_id,
            created_by_id=ticket.created_by_id,
            branch_id=ticket.branch_id,
            created_at=ticket.created_at,
            status=ticket.status,
            priority=ticket.priority,
            error=ticket.error,
            error_description=ticket.error_description,
            accessories=ticket.accessories,
            internal_notes=ticket.internal_notes,
            estimated_cost=float(ticket.estimated_cost),
            actual_cost=float(ticket.actual_cost),
            deposit_paid=float(ticket.deposit_paid),
            assigned_technician_id=ticket.assigned_technician_id,
            deadline=ticket.deadline,
            completed_at=ticket.completed_at,
            warranty_covered=ticket.warranty_covered,
            approved_by_id=ticket.approved_by_id,
            is_deleted=ticket.is_deleted if hasattr(ticket, 'is_deleted') else False,
            deleted_at=ticket.deleted_at if hasattr(ticket, 'deleted_at') else None,
            # Related objects
            device=DeviceDTO.from_model(ticket.device) if ticket.device else None,
            customer=CustomerDTO.from_model(ticket.device.customer) if ticket.device and ticket.device.customer else None,
            technician_name=ticket.assigned_technician.full_name if ticket.assigned_technician and ticket.assigned_technician.full_name else None,
            created_by_name=ticket.created_by.full_name if ticket.created_by else None
        )
    
    def to_dict(self) -> dict:
        """Convert DTO to dictionary for service/repository use"""
        return {
            'device_id': self.device_id,
            'created_by_id': self.created_by_id,
            'branch_id': self.branch_id,
            'status': self.status,
            'priority': self.priority,
            'error': self.error,
            'error_description': self.error_description,
            'accessories': self.accessories,
            'internal_notes': self.internal_notes,
            'estimated_cost': self.estimated_cost,
            'actual_cost': self.actual_cost,
            'deposit_paid': self.deposit_paid,
            'assigned_technician_id': self.assigned_technician_id,
            'deadline': self.deadline,
            'warranty_covered': self.warranty_covered,
            'approved_by_id': self.approved_by_id
        }
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging"""
        return {
            'ticket_id': self.id,
            'ticket_number': self.ticket_number,
            'status': self.status,
            'priority': self.priority,
            'error': self.error,
            'error_description': self.error_description,
            'accessories': self.accessories,
            'internal_notes': self.internal_notes,
            'estimated_cost': float(self.estimated_cost),
            'actual_cost': float(self.actual_cost),
            'deposit_paid': float(self.deposit_paid),
            'assigned_technician_id': self.assigned_technician_id,
            'device_id': self.device_id,
            'created_by_id': self.created_by_id,
            'branch_id': self.branch_id,
            'approved_by_id': self.approved_by_id,
            'warranty_covered': self.warranty_covered,
            'is_deleted': self.is_deleted,
            'deadline': self.deadline.isoformat() if hasattr(self.deadline, 'isoformat') else self.deadline,
            'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else self.created_at,
            'completed_at': self.completed_at.isoformat() if hasattr(self.completed_at, 'isoformat') else self.completed_at,
            'deleted_at': self.deleted_at.isoformat() if hasattr(self.deleted_at, 'isoformat') else self.deleted_at
        }