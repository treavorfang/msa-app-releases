"""WorkLog DTO - Data Transfer Object."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WorkLogDTO:
    """Data Transfer Object for WorkLog."""
    
    id: Optional[int] = None
    technician_id: Optional[int] = None
    ticket_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    work_performed: str = ""
    
    # Flattened
    technician_name: Optional[str] = None
    ticket_number: Optional[str] = None
    
    # Computed
    duration_minutes: float = 0.0

    @classmethod
    def from_model(cls, log) -> 'WorkLogDTO':
        """Convert model to DTO."""
        duration = 0.0
        if log.end_time and log.start_time:
            delta = log.end_time - log.start_time
            duration = delta.total_seconds() / 60.0
            
        dto = cls(
            id=log.id,
            technician_id=log.technician_id if log.technician else None,
            ticket_id=log.ticket_id if log.ticket else None,
            start_time=log.start_time,
            end_time=log.end_time,
            work_performed=log.work_performed,
            technician_name=log.technician.full_name if log.technician else None,
            ticket_number=log.ticket.ticket_number if log.ticket else None,
            duration_minutes=round(duration, 2)
        )
        return dto
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'log_id': self.id,
            'ticket_id': self.ticket_id,
            'technician_id': self.technician_id,
            'work_performed': self.work_performed,
            'start_time': self.start_time.isoformat() if hasattr(self.start_time, 'isoformat') else self.start_time,
            'end_time': self.end_time.isoformat() if hasattr(self.end_time, 'isoformat') else self.end_time,
            'duration_minutes': self.duration_minutes
        }
