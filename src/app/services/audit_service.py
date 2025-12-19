"""AuditService - Security and Action Logging.

This service handles the creation and retrieval of audit logs for all system actions.
It implements the IAuditService interface and provides methods for tracking user activity
and data changes.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from models.audit_log import AuditLog
from models.user import User
from interfaces.iaudit_service import IAuditService


class AuditService(IAuditService):
    """Service class for Audit Log operations.
    
    Methods are static to allow easy usage, though the service is typically instantiated
    and injected into other services.
    """
    
    @staticmethod
    def log_action(
        user: Optional[User],
        action: str,
        table_name: str,
        old_data: Optional[dict] = None,
        new_data: Optional[dict] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Log a system action to the database.
        
        Args:
            user: User performing the action (optional for system actions)
            action: Description of the action (e.g., 'create', 'update')
            table_name: Affected table or entity name
            old_data: Dictionary of data before change
            new_data: Dictionary of data after change
            ip_address: Client IP address
            
        Returns:
            AuditLog: The created log entry
        """
        # Handle UserDTO vs User model
        user_id = None
        if user is not None:
            # Check if it's a DTO (has 'id' attribute but not a Peewee model)
            if hasattr(user, 'id') and not isinstance(user, User):
                user_id = user.id
                user = None  # Don't pass DTO to Peewee
            elif isinstance(user, User):
                user_id = user.id
        
        return AuditLog.create(
            user=user_id,
            action=action,
            table_name=table_name,
            old_data=old_data,
            new_data=new_data,
            ip_address=ip_address
        )

    @staticmethod
    def get_logs_for_user(user_id: int, limit: int = 100) -> List[AuditLog]:
        """Retrieve recent logs for a specific user."""
        query = AuditLog.select().where(AuditLog.user == user_id)
        return query.order_by(AuditLog.created_at.desc()).limit(limit)

    @staticmethod
    def get_logs_for_table(table_name: str, limit: int = 100) -> List[AuditLog]:
        """Retrieve recent logs for a specific table."""
        query = AuditLog.select().where(AuditLog.table_name == table_name)
        return query.order_by(AuditLog.created_at.desc()).limit(limit)

    @staticmethod
    def get_recent_logs(
        days: int = 7,
        user_id: Optional[int] = None,
        table_name: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """Retrieve recent logs with optional filtering.
        
        Args:
            days: Number of past days to search
            user_id: Filter by user ID
            table_name: Filter by table name
            action: Filter by action type
            limit: Max results to return
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        query = AuditLog.select().where(AuditLog.created_at >= cutoff_date)

        if user_id:
            query = query.where(AuditLog.user == user_id)
        if table_name:
            query = query.where(AuditLog.table_name == table_name)
        if action:
            query = query.where(AuditLog.action == action)

        return query.order_by(AuditLog.created_at.desc()).limit(limit)