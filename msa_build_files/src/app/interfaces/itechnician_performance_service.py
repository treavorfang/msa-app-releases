"""ITechnicianPerformanceService - Interface for Performance Service."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import date
from dtos.technician_performance_dto import TechnicianPerformanceDTO

class ITechnicianPerformanceService(ABC):
    @abstractmethod
    def calculate_monthly_performance(self, technician_id: int, month: date) -> TechnicianPerformanceDTO:
        pass
        
    @abstractmethod
    def get_performance(self, technician_id: int, month: date) -> TechnicianPerformanceDTO:
        pass
        
    @abstractmethod
    def get_performance_history(self, technician_id: int, months: int = 12) -> List[TechnicianPerformanceDTO]:
        pass
        
    @abstractmethod
    def get_year_to_date_summary(self, technician_id: int) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    def recalculate_all_months(self, technician_id: int, start_month: Optional[date] = None) -> None:
        pass
        
    @abstractmethod
    def get_team_comparison(self, month: Optional[date] = None) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def get_top_performers(self, month: Optional[date] = None, limit: int = 5) -> List[Dict[str, Any]]:
        pass
