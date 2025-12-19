# src/app/core/core_services.py
from services.audit_service import AuditService
from services.role_service import RoleService
from services.system_monitor_service import SystemMonitorService
from interfaces.iaudit_service import IAuditService
from interfaces.irole_service import IRoleService

class CoreServices:
    def __init__(self):
        """Initialize services that don't have external dependencies"""
        self._audit_service: IAuditService = AuditService()
        self._role_service: IRoleService = RoleService(self._audit_service)
        self._system_monitor_service = SystemMonitorService()

    @property
    def audit_service(self) -> IAuditService:
        return self._audit_service
    
    @property
    def role_service(self) -> IRoleService:
        return self._role_service

    @property
    def system_monitor_service(self) -> SystemMonitorService:
        return self._system_monitor_service