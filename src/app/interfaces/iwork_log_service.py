"""IWorkLogService - Interface for Work Log Service."""

from abc import ABC, abstractmethod
from typing import Optional, List
from dtos.work_log_dto import WorkLogDTO

class IWorkLogService(ABC):
    @abstractmethod
    def start_work_log(self, technician_id: int, ticket_id: int, description: str, current_user=None, ip_address=None) -> WorkLogDTO:
        pass
        
    @abstractmethod
    def end_work_log(self, work_log_id: int, current_user=None, ip_address=None) -> Optional[WorkLogDTO]:
        pass
        
    @abstractmethod
    def update_work_description(self, work_log_id: int, description: str, current_user=None, ip_address=None) -> Optional[WorkLogDTO]:
        pass
        
    @abstractmethod
    def get_active_logs_for_technician(self, technician_id: int) -> List[WorkLogDTO]:
        pass
        
    @abstractmethod
    def get_logs_for_ticket(self, ticket_id: int) -> List[WorkLogDTO]:
        pass
        
    @abstractmethod
    def calculate_time_spent(self, ticket_id: int) -> float:
        pass