# src/app/interfaces/iticket_service.py
from abc import ABC, abstractmethod
from typing import List, Optional
from dtos.ticket_dto import TicketDTO

class ITicketService(ABC):
    @abstractmethod
    def create_ticket(self, ticket_data: dict) -> TicketDTO:
        pass
        
    @abstractmethod
    def get_ticket(self, ticket_id: int, include_deleted: bool = False) -> Optional[TicketDTO]:
        pass
        
    @abstractmethod
    def update_ticket(self, ticket_id: int, update_data: dict) -> Optional[TicketDTO]:
        pass
        
    @abstractmethod
    def delete_ticket(self, ticket_id: int) -> bool:
        pass
        
    @abstractmethod
    def restore_ticket(self, ticket_id: int) -> bool:
        """Restore a soft-deleted ticket"""
        pass
        
    @abstractmethod
    def list_tickets(self, filters: dict = None) -> List[TicketDTO]:
        pass
        
    @abstractmethod
    def search_tickets(self, search_term: str) -> List[TicketDTO]:
        pass
        
    @abstractmethod
    def change_ticket_status(self, ticket_id: int, new_status: str, reason: str = None, current_user=None, ip_address=None) -> Optional[TicketDTO]:
        pass
        
    @abstractmethod
    def assign_ticket(self, ticket_id: int, technician_id: int) -> Optional[TicketDTO]:
        pass
        
    @abstractmethod
    def get_dashboard_stats(self, date=None) -> dict:
        pass
        
    @abstractmethod
    def get_recent_tickets(self, limit: int = 10) -> List[TicketDTO]:
        pass
    
    # Enhanced dashboard methods
    @abstractmethod
    def get_dashboard_stats_range(self, start_date, end_date) -> dict:
        pass
    
    @abstractmethod
    def get_technician_performance(self, start_date, end_date) -> List[dict]:
        pass
    
    @abstractmethod
    def get_status_distribution(self, start_date, end_date) -> dict:
        pass
    
    @abstractmethod
    def get_revenue_trend(self, start_date, end_date) -> List[dict]:
        pass
    
    @abstractmethod
    def get_average_completion_time(self, start_date, end_date) -> float:
        pass