"""WorkLog Repository - Work Logging Data Access Layer.

This repository handles all database operations for WorkLog entities.
Tracks time spent by technicians on tickets.
"""

from typing import Optional, List
from peewee import fn
from models.work_log import WorkLog


class WorkLogRepository:
    """Repository for WorkLog data access operations."""
    
    def create(self, work_log_data: dict) -> WorkLog:
        """Create a new work log entry."""
        return WorkLog.create(**work_log_data)
    
    def get(self, work_log_id: int) -> Optional[WorkLog]:
        """Get work log by ID."""
        try:
            return WorkLog.get_by_id(work_log_id)
        except WorkLog.DoesNotExist:
            return None
    
    def update(self, work_log_id: int, update_data: dict) -> Optional[WorkLog]:
        """Update work log details."""
        try:
            work_log = WorkLog.get_by_id(work_log_id)
            for key, value in update_data.items():
                setattr(work_log, key, value)
            work_log.save()
            return work_log
        except WorkLog.DoesNotExist:
            return None
    
    def get_active_for_technician(self, technician_id: int) -> List[WorkLog]:
        """Get currently active (unfinished) work logs for a technician."""
        return list(WorkLog.select().where(
            (WorkLog.technician == technician_id) &
            (WorkLog.end_time.is_null())
        ))
    
    def get_for_ticket(self, ticket_id: int) -> List[WorkLog]:
        """Get all work logs for a specific ticket."""
        return list(WorkLog.select().where(WorkLog.ticket == ticket_id))
    
    def get_total_time_for_ticket(self, ticket_id: int) -> float:
        """Calculate total time spent on a ticket in seconds."""
        result = (WorkLog
                 .select(fn.SUM(
                     fn.strftime('%s', WorkLog.end_time) - 
                     fn.strftime('%s', WorkLog.start_time)
                 ))
                 .where(
                     (WorkLog.ticket == ticket_id) &
                     (WorkLog.end_time.is_null(False)))
                 .scalar())
        return result or 0.0