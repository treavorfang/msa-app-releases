# =============================================================================
# FILE: src/app/services/iaudit_service.py
#
# PURPOSE: Defines the interface for audit logging services.
#
# METHODS:
#   - log_action: Logs a user action to the audit log
#   - get_logs_for_user: Retrieves audit logs for a specific user
#   - get_logs_for_table: Retrieves audit logs for a specific table
#   - get_recent_logs: Gets recent audit logs with optional filters
# =============================================================================

from typing import Optional, List
from datetime import datetime
from models.audit_log import AuditLog
from models.user import User

class IAuditService:
    @staticmethod
    def log_action(
        user: Optional[User],
        action: str,
        table_name: str,
        old_data: Optional[dict] = None,
        new_data: Optional[dict] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Logs an action to the audit log.
        
        Args:
            user: The user performing the action (None for system actions)
            action: Description of the action (e.g., "create", "update", "delete")
            table_name: Name of the table being modified
            old_data: Data before the change (for updates/deletes)
            new_data: Data after the change (for creates/updates)
            ip_address: IP address of the user
            
        Returns:
            The created AuditLog record
        """
        raise NotImplementedError

    @staticmethod
    def get_logs_for_user(user_id: int, limit: int = 100) -> List[AuditLog]:
        """
        Gets audit logs for a specific user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of logs to return
            
        Returns:
            List of AuditLog records
        """
        raise NotImplementedError

    @staticmethod
    def get_logs_for_table(table_name: str, limit: int = 100) -> List[AuditLog]:
        """
        Gets audit logs for a specific table.
        
        Args:
            table_name: Name of the table
            limit: Maximum number of logs to return
            
        Returns:
            List of AuditLog records
        """
        raise NotImplementedError

    @staticmethod
    def get_recent_logs(
        days: int = 7,
        user_id: Optional[int] = None,
        table_name: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Gets recent audit logs with optional filters.
        
        Args:
            days: Number of past days to include
            user_id: Optional user ID filter
            table_name: Optional table name filter
            action: Optional action type filter
            limit: Maximum number of logs to return
            
        Returns:
            List of filtered AuditLog records
        """
        raise NotImplementedError