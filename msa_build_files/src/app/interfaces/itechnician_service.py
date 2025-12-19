"""ITechnicianService - Interface for Technician Service."""

from abc import ABC, abstractmethod
from typing import Optional, List
from dtos.technician_dto import TechnicianDTO

class ITechnicianService(ABC):
    @abstractmethod
    def create_technician(self, technician_data: dict, current_user=None, ip_address=None) -> TechnicianDTO:
        pass
        
    @abstractmethod
    def get_technician(self, technician_id: int) -> Optional[TechnicianDTO]:
        pass
        
    @abstractmethod
    def update_technician(self, technician_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[TechnicianDTO]:
        pass
        
    @abstractmethod
    def delete_technician(self, technician_id: int, current_user=None, ip_address=None) -> bool:
        pass
        
    @abstractmethod
    def get_all_technicians(self) -> List[TechnicianDTO]:
        pass
        
    @abstractmethod
    def get_active_technicians(self) -> List[TechnicianDTO]:
        pass
        
    @abstractmethod
    def search_technicians(self, query: str) -> List[TechnicianDTO]:
        pass