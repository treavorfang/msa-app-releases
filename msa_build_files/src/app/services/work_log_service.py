"""WorkLogService - Technician Labor and Time Tracking.

This service manages work logs using DTOs.
"""

from typing import List, Optional, Any, Dict
from datetime import datetime
from interfaces.iwork_log_service import IWorkLogService
from repositories.work_log_repository import WorkLogRepository
from models.work_log import WorkLog
from services.audit_service import AuditService
from dtos.work_log_dto import WorkLogDTO


class WorkLogService(IWorkLogService):
    """Service class for Work Log operations."""
    
    def __init__(self, audit_service: AuditService):
        """Initialize WorkLogService."""
        self.repository = WorkLogRepository()
        self.audit_service = audit_service
        
    def start_work_log(self, technician_id: int, ticket_id: int, description: str, 
                      current_user=None, ip_address=None) -> WorkLogDTO:
        """Start a new work session."""
        # End any existing active logs
        active_logs = self.repository.get_active_for_technician(technician_id)
        for log in active_logs:
            self._end_work_log_internal(log.id, current_user, ip_address)
        
        # Start new log
        work_log = self.repository.create({
            'technician': technician_id,
            'ticket': ticket_id,
            'work_performed': description
        })
        
        dto = WorkLogDTO.from_model(work_log)
        
        self.audit_service.log_action(
            user=current_user,
            action="work_log_start",
            table_name="work_logs",
            new_data={
                'work_log_id': work_log.id,
                'technician_id': technician_id,
                'ticket_id': ticket_id
            },
            ip_address=ip_address
        )
        return dto
        
    def end_work_log(self, work_log_id: int, current_user=None, ip_address=None) -> Optional[WorkLogDTO]:
        """End an specific active work log."""
        wl = self._end_work_log_internal(work_log_id, current_user, ip_address)
        return WorkLogDTO.from_model(wl) if wl else None
        
    def _end_work_log_internal(self, work_log_id: int, current_user=None, ip_address=None) -> Optional[WorkLog]:
        """Internal method to end a work log."""
        work_log = self.repository.update(work_log_id, {'end_time': datetime.now()})
        if work_log:
            self.audit_service.log_action(
                user=current_user,
                action="work_log_end",
                table_name="work_logs",
                record_id=work_log_id,
                new_data={
                    'duration_minutes': self._calculate_duration_minutes(work_log),
                    'ticket_id': work_log.ticket.id if work_log.ticket else None
                },
                ip_address=ip_address
            )
        return work_log
        
    def update_work_description(self, work_log_id: int, description: str,
                              current_user=None, ip_address=None) -> Optional[WorkLogDTO]:
        """Update the description of a work log entry."""
        old_log = self.repository.get(work_log_id)
        if not old_log:
            return None
            
        old_dto = WorkLogDTO.from_model(old_log)
        work_log = self.repository.update(work_log_id, {'work_performed': description})
        
        if work_log:
            new_dto = WorkLogDTO.from_model(work_log)
            self.audit_service.log_action(
                user=current_user,
                action="work_log_update",
                table_name="work_logs",
                record_id=work_log_id,
                old_data={'description': old_dto.work_performed},
                new_data={'description': description},
                ip_address=ip_address
            )
            return new_dto
        return None
        
    def get_active_logs_for_technician(self, technician_id: int) -> List[WorkLogDTO]:
        """Get currently active (running) logs for a technician."""
        logs = self.repository.get_active_for_technician(technician_id)
        return [WorkLogDTO.from_model(log) for log in logs]
        
    def get_logs_for_technician(self, technician_id: int, limit: int = 100) -> List[WorkLogDTO]:
        """Get all work logs for a technician (history)."""
        # Using repository to fetch (assuming get_by_technician exists or using filter)
        # Often Repositories have generic filter methods. If not, we might need to add it to Repo.
        # Assuming filtering capabilities similar to TicketRepository
        try:
             # Try specific method first if it exists
             if hasattr(self.repository, 'get_by_technician'):
                 logs = self.repository.get_by_technician(technician_id, limit)
             else:
                 # Fallback to direct query or generic list
                 # Note: self.repository is WorkLogRepository
                 # Let's use a safe assumption that we can query via model if needed, but Service shouldn't use Model directly ideally.
                 # Best effort: use get_active_for_technician as template? No that's only active.
                 # Let's assume list_all supports filter 'technician'
                 if hasattr(self.repository, 'list_all'):
                     logs = self.repository.list_all({'technician': technician_id})
                     if limit: logs = logs[:limit]
                 else:
                     # Fallback: return empty if we can't query effectively without breaking architecture
                     # or implement a direct query here if absolutely necessary (Peewee)
                     from models.work_log import WorkLog
                     logs = list(WorkLog.select().where(WorkLog.technician == technician_id).order_by(WorkLog.start_time.desc()).limit(limit))
        except Exception:
            # Fallback for safety
            from models.work_log import WorkLog
            logs = list(WorkLog.select().where(WorkLog.technician == technician_id).order_by(WorkLog.start_time.desc()).limit(limit))
            
        return [WorkLogDTO.from_model(log) for log in logs]
        
    def get_logs_for_ticket(self, ticket_id: int) -> List[WorkLogDTO]:
        """Get all work logs associated with a ticket."""
        logs = self.repository.get_for_ticket(ticket_id)
        return [WorkLogDTO.from_model(log) for log in logs]
        
    def calculate_time_spent(self, ticket_id: int) -> float:
        """Calculate total time spent on a ticket in minutes."""
        total_seconds = self.repository.get_total_time_for_ticket(ticket_id)
        return round(total_seconds / 60, 2)
        
    def _calculate_duration_minutes(self, work_log: WorkLog) -> float:
        """Calculate duration of a finished work log in minutes."""
        if not work_log.end_time:
            return 0.0
        duration = (work_log.end_time - work_log.start_time).total_seconds()
        return round(duration / 60, 2)