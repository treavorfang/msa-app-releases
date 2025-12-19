"""RepairPartService - Repair Part Management Business Logic.

This service manages the tracking of parts used in repair tickets.
It handles stock validation, reduction upon use, and restoration upon deletion.
"""

from typing import Optional, List, Dict, Any
from models.repair_part import RepairPart
from models.ticket import Ticket
from models.part import Part
from models.user import User
from models.technician import Technician
from interfaces.irepair_part_service import IRepairPartService
from interfaces.ipart_service import IPartService
from repositories.repair_part_repository import RepairPartRepository
from services.audit_service import AuditService


from dtos.repair_part_dto import RepairPartDTO

class RepairPartService(IRepairPartService):
    """Service class for Repair Part operations."""
    
    def __init__(self, audit_service: AuditService, part_service: IPartService = None):
        """Initialize RepairPartService.
        
        Args:
            audit_service: Service for logging security/audit events
            part_service: Service for inventory updates (required for stock management)
        """
        self._audit_service = audit_service
        self._part_service = part_service
        self._audit_service = audit_service
        self._part_service = part_service
        self._repository = RepairPartRepository()
        
        # Internal repositories for model lookup
        from repositories.ticket_repository import TicketRepository
        from repositories.part_repository import PartRepository
        from repositories.technician_repository import TechnicianRepository
        self._ticket_repo = TicketRepository()
        self._part_repo = PartRepository()
        self._tech_repo = TechnicianRepository()

    def create_repair_part(
        self,
        ticket_id: int,
        part_id: int,
        technician_id: Optional[int],
        current_user: Optional[User] = None,
        quantity: int = 1,
        notes: Optional[str] = None
    ) -> RepairPartDTO:
        """Record usage of a part in a repair ticket."""
        # Lookup models
        ticket = self._ticket_repo.get(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
            
        part = self._part_repo.get_part_by_id(part_id)
        if not part:
            raise ValueError(f"Part {part_id} not found")
            
        technician = None
        if technician_id:
            technician = self._tech_repo.get(technician_id)
            
        # Check part stock before creating
        if part.current_stock < quantity:
            raise ValueError(f"Not enough stock. Available: {part.current_stock}, Requested: {quantity}")
        
        repair_part = self._repository.create_repair_part(
            ticket=ticket,
            part=part,
            technician=technician,
            quantity=quantity,
            notes=notes
        )
        
        dto = RepairPartDTO.from_model(repair_part)
        
        # Log the creation
        self._audit_service.log_action(
            user=current_user,
            action="create",
            table_name="repair_parts",
            new_data=dto.to_audit_dict()
        )
        
        # Update stock if part service is available
        if self._part_service:
            self._part_service.update_stock(
                part.id, 
                -quantity,
                reference_type='repair_ticket',
                reference_id=ticket.id,
                notes=f"Used in repair ticket #{ticket.ticket_number}",
                user=current_user
            )
        
        return dto
    
    def get_repair_part_by_id(self, repair_part_id: int) -> Optional[RepairPartDTO]:
        """Get a repair part record by ID."""
        model = self._repository.get_repair_part_by_id(repair_part_id)
        return RepairPartDTO.from_model(model) if model else None
    
    def get_parts_used_in_ticket(self, ticket_id: int) -> List[RepairPartDTO]:
        """Get all parts used in a specific ticket."""
        models = self._repository.get_parts_used_in_ticket(ticket_id)
        return [RepairPartDTO.from_model(m) for m in models]
    
    def get_repairs_using_part(self, part_id: int) -> List[RepairPartDTO]:
        """Get all repair records where a specific part was used."""
        models = self._repository.get_repairs_using_part(part_id)
        return [RepairPartDTO.from_model(m) for m in models]
    
    def update_repair_part(self, repair_part_id: int, **kwargs) -> Optional[RepairPartDTO]:
        """Update a repair part record."""
        old_repair_part = self._repository.get_repair_part_by_id(repair_part_id)
        if not old_repair_part:
            return None
            
        old_dto = RepairPartDTO.from_model(old_repair_part)
                 
        repair_part = self._repository.update_repair_part(repair_part_id, **kwargs)
        
        if repair_part:
            new_dto = RepairPartDTO.from_model(repair_part)
            self._audit_service.log_action(
                user=None,  # TODO: Update signature to accept user
                action="update",
                table_name="repair_parts",
                old_data=old_dto.to_audit_dict(),
                new_data=new_dto.to_audit_dict()
            )
            return new_dto
        return None
    
    def delete_repair_part(self, repair_part_id: int, user: Optional[User] = None) -> bool:
        """Delete a repair part record and restore stock."""
        repair_part = self._repository.get_repair_part_by_id(repair_part_id)
        if not repair_part:
            return False
            
        dto = RepairPartDTO.from_model(repair_part)
            
        result = self._repository.delete_repair_part(repair_part_id)
        if result:
            self._audit_service.log_action(
                user=user,
                action="delete",
                table_name="repair_parts",
                old_data=dto.to_audit_dict()
            )
            
            # Restore stock if part service is available
            if self._part_service:
                self._part_service.update_stock(
                    repair_part.part.id, 
                    repair_part.quantity,
                    reference_type='repair_ticket',
                    reference_id=repair_part.ticket.id,
                    notes=f"Restored from deleted repair ticket #{repair_part.ticket.ticket_number}",
                    user=user
                )
                
        return result