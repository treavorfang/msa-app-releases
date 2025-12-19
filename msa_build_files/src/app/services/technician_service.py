"""TechnicianService - Technician Management Logic.

This service manages technician profiles using DTOs.
"""

from typing import List, Optional, Any, Dict
from interfaces.itechnician_service import ITechnicianService
from repositories.technician_repository import TechnicianRepository
from models.technician import Technician
from services.audit_service import AuditService
from dtos.technician_dto import TechnicianDTO


class TechnicianService(ITechnicianService):
    """Service class for Technician operations."""
    
    def __init__(self, audit_service: AuditService):
        """Initialize TechnicianService."""
        self.repository = TechnicianRepository()
        self.audit_service = audit_service
        
    def create_technician(self, technician_data: dict, current_user=None, ip_address=None) -> TechnicianDTO:
        """Create a new technician profile."""
        technician = self.repository.create(technician_data)
        dto = TechnicianDTO.from_model(technician)
        
        self.audit_service.log_action(
            user=current_user,
            action="technician_create",
            table_name="technicians",
            new_data=dto.to_audit_dict(),
            ip_address=ip_address
        )
        return dto
        
    def get_technician(self, technician_id: int) -> Optional[TechnicianDTO]:
        """Get a technician by ID."""
        tech = self.repository.get(technician_id)
        return TechnicianDTO.from_model(tech) if tech else None
        
    def get_technician_by_user(self, user_id: int) -> Optional[TechnicianDTO]:
        """Get a technician profile linked to a user ID."""
        tech = self.repository.get_by_user(user_id)
        return TechnicianDTO.from_model(tech) if tech else None
        
    def update_technician(self, technician_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[TechnicianDTO]:
        """Update a technician's profile."""
        old_tech = self.repository.get(technician_id)
        if not old_tech:
            return None
            
        old_dto = TechnicianDTO.from_model(old_tech)
        technician = self.repository.update(technician_id, update_data)
        
        if technician:
            new_dto = TechnicianDTO.from_model(technician)
            self.audit_service.log_action(
                user=current_user,
                action="technician_update",
                table_name="technicians",
                old_data=old_dto.to_audit_dict(),
                new_data=new_dto.to_audit_dict(),
                ip_address=ip_address
            )
            return new_dto
        return None
        
    def delete_technician(self, technician_id: int, current_user=None, ip_address=None) -> bool:
        """Deactivate a technician (soft delete)."""
        tech = self.repository.get(technician_id)
        if not tech:
            return False
            
        dto = TechnicianDTO.from_model(tech)
        # Using deactivate typically
        success = self.repository.deactivate(technician_id)
        
        if success:
            self.audit_service.log_action(
                user=current_user,
                action="technician_delete",
                table_name="technicians",
                old_data=dto.to_audit_dict(),
                ip_address=ip_address
            )
        return success
        
    def get_all_technicians(self) -> List[TechnicianDTO]:
        """List all technicians."""
        # Defaults to all (both active and inactive usually, or just active? Interface said get_all)
        # Service list_technicians had active_only default True.
        # I'll implement get_all (all) and get_active separately or via argument 
        # But Interface defined get_all and get_active
        techs = self.repository.list_all(active_only=False)
        return [TechnicianDTO.from_model(t) for t in techs]
        
    def get_active_technicians(self) -> List[TechnicianDTO]:
        """List active technicians."""
        techs = self.repository.list_all(active_only=True)
        return [TechnicianDTO.from_model(t) for t in techs]
        
    def search_technicians(self, query: str) -> List[TechnicianDTO]:
        """Search technicians."""
        techs = self.repository.search(query)
        return [TechnicianDTO.from_model(t) for t in techs]