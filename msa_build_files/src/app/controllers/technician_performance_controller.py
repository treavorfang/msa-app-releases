"""TechnicianPerformanceController - Bridge between UI and Service."""

from PySide6.QtCore import QObject, Signal
from typing import List, Optional, Dict, Any
from datetime import date
from dtos.technician_performance_dto import TechnicianPerformanceDTO

class TechnicianPerformanceController(QObject):
    """Controller for managing technician performance."""
    
    performance_updated = Signal()
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.service = container.technician_performance_service
    
    def calculate_monthly_performance(self, technician_id: int, month: date) -> TechnicianPerformanceDTO:
        """Calculate and save performance metrics."""
        perf = self.service.calculate_monthly_performance(technician_id, month)
        self.performance_updated.emit()
        return perf
    
    def get_performance(self, technician_id: int, month: date) -> TechnicianPerformanceDTO:
        """Get performance record."""
        return self.service.get_performance(technician_id, month)
    
    def get_performance_history(self, technician_id: int, months: int = 12) -> List[TechnicianPerformanceDTO]:
        """Get performance history."""
        return self.service.get_performance_history(technician_id, months)
    
    def get_year_to_date_summary(self, technician_id: int) -> Dict[str, Any]:
        """Get YTD summary."""
        return self.service.get_year_to_date_summary(technician_id)
    
    def recalculate_all_months(self, technician_id: int, start_month: date = None):
        """Recalculate performance for all months."""
        self.service.recalculate_all_months(technician_id, start_month)
        self.performance_updated.emit()
    
    def get_team_comparison(self, month: date = None) -> List[Dict[str, Any]]:
        """Get team comparison."""
        return self.service.get_team_comparison(month)
    
    def get_top_performers(self, month: date = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performers."""
        return self.service.get_top_performers(month, limit)
