"""StatusHistory Repository - Status Change Tracking Data Access Layer.

This repository handles all database operations for StatusHistory entities.
Tracks lifecycle changes of tickets.
"""

from typing import List, Optional
from models.status_history import StatusHistory


class StatusHistoryRepository:
    """Repository for StatusHistory data access operations."""
    
    def create_status_history(self, history_data: dict) -> StatusHistory:
        """Create a new status history entry."""
        return StatusHistory.create(**history_data)
    
    def get_history_for_ticket(self, ticket_id: int, limit: int = 100) -> List[StatusHistory]:
        """Get status history for a specific ticket."""
        return list(StatusHistory.select()
                   .where(StatusHistory.ticket == ticket_id)
                   .order_by(StatusHistory.changed_at.desc())
                   .limit(limit))
    
    def get_latest_status_change(self, ticket_id: int) -> Optional[StatusHistory]:
        """Get the most recent status change for a ticket."""
        return (StatusHistory.select()
               .where(StatusHistory.ticket == ticket_id)
               .order_by(StatusHistory.changed_at.desc())
               .first())
