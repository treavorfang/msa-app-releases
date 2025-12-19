"""WorkLogController - Bridge between UI and WorkLogService."""

from PySide6.QtCore import QObject, Signal
from typing import List, Optional
from dtos.work_log_dto import WorkLogDTO


class WorkLogController(QObject):
    """Controller for Work Log management."""
    
    # Signals now emit DTOs
    work_started = Signal(object)
    work_ended = Signal(object)
    work_updated = Signal(object)
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.work_log_service = container.work_log_service
        self.current_user = getattr(container, 'current_user', None)
        
    def start_work_log(self, technician_id: int, ticket_id: int, description: str) -> Optional[WorkLogDTO]:
        """Start a work log."""
        work_log = self.work_log_service.start_work_log(
            technician_id, 
            ticket_id, 
            description, 
            current_user=self.current_user
        )
        if work_log:
            self.work_started.emit(work_log)
        return work_log
        
    def end_work_log(self, work_log_id: int) -> Optional[WorkLogDTO]:
        """End a work log."""
        work_log = self.work_log_service.end_work_log(
            work_log_id, 
            current_user=self.current_user
        )
        if work_log:
            self.work_ended.emit(work_log)
        return work_log
        
    def update_work_description(self, work_log_id: int, description: str) -> Optional[WorkLogDTO]:
        """Update description."""
        work_log = self.work_log_service.update_work_description(
            work_log_id, 
            description, 
            current_user=self.current_user
        )
        if work_log:
            self.work_updated.emit(work_log)
        return work_log
        
    def get_active_logs_for_technician(self, technician_id: int) -> List[WorkLogDTO]:
        """Get active logs."""
        return self.work_log_service.get_active_logs_for_technician(technician_id)
        
    def get_logs_for_ticket(self, ticket_id: int) -> List[WorkLogDTO]:
        """Get logs for ticket."""
        return self.work_log_service.get_logs_for_ticket(ticket_id)
        
    def calculate_time_spent(self, ticket_id: int) -> float:
        """Calculate time spent."""
        return self.work_log_service.calculate_time_spent(ticket_id)