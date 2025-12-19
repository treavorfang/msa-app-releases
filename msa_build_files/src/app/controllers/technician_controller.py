"""TechnicianController - Bridge between UI and TechnicianService."""

from PySide6.QtCore import QObject, Signal
from typing import List, Optional
from dtos.technician_dto import TechnicianDTO
from core.event_bus import EventBus
from core.events import TechnicianCreatedEvent, TechnicianUpdatedEvent, TechnicianDeactivatedEvent

class TechnicianController(QObject):
    """Controller for Technician management."""
    
    # Signals now emit DTOs
    technician_created = Signal(object)
    technician_updated = Signal(object)
    technician_deactivated = Signal(int)
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.technician_service = container.technician_service
        self.current_user = getattr(container, 'current_user', None)
        
    def create_technician(self, technician_data: dict) -> Optional[TechnicianDTO]:
        """Create a new technician."""
        # user_id arg was present in old signature but unused or implicit? 
        # Making consistent with other controllers: pass data and current_user
        technician = self.technician_service.create_technician(
            technician_data, 
            current_user=self.current_user
        )
        if technician:
            self.technician_created.emit(technician)
            user_id = self.current_user.id if self.current_user else None
            EventBus.publish(TechnicianCreatedEvent(technician.id, user_id))
        return technician
        
    def get_technician(self, technician_id: int) -> Optional[TechnicianDTO]:
        """Get a technician by ID."""
        return self.technician_service.get_technician(technician_id)
        
    def get_technician_by_user(self, user_id: int) -> Optional[TechnicianDTO]:
        """Get technician by user ID."""
        return self.technician_service.get_technician_by_user(user_id)
        
    def update_technician(self, technician_id: int, update_data: dict) -> Optional[TechnicianDTO]:
        """Update a technician."""
        technician = self.technician_service.update_technician(
            technician_id, 
            update_data, 
            current_user=self.current_user
        )
        if technician:
            self.technician_updated.emit(technician)
            EventBus.publish(TechnicianUpdatedEvent(technician.id))
        return technician
        
    def deactivate_technician(self, technician_id: int) -> bool:
        """Deactivate a technician."""
        success = self.technician_service.delete_technician(
            technician_id, 
            current_user=self.current_user
        )
        if success:
            self.technician_deactivated.emit(technician_id)
            EventBus.publish(TechnicianDeactivatedEvent(technician_id))
        return success
        
    def list_technicians(self, active_only: bool = True) -> List[TechnicianDTO]:
        """List technicians."""
        if active_only:
            return self.technician_service.get_active_technicians()
        return self.technician_service.get_all_technicians()
        
    def search_technicians(self, search_term: str) -> List[TechnicianDTO]:
        """Search technicians."""
        return self.technician_service.search_technicians(search_term)