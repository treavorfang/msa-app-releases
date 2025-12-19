# src/app/interfaces/irepair_part_service.py
from typing import Optional, List
from models.repair_part import RepairPart
from models.ticket import Ticket
from models.part import Part
from models.user import User
from models.technician import Technician

class IRepairPartService:
    def create_repair_part(
        self,
        ticket: Ticket,
        part: Part,
        technician: Optional[Technician],
        current_user: Optional[User] = None,
        quantity: int = 1,
        notes: Optional[str] = None
    ) -> RepairPart:
        raise NotImplementedError
    
    def get_repair_part_by_id(self, repair_part_id: int) -> Optional[RepairPart]:
        raise NotImplementedError
    
    def get_parts_used_in_ticket(self, ticket_id: int) -> List[RepairPart]:
        raise NotImplementedError
    
    def get_repairs_using_part(self, part_id: int) -> List[RepairPart]:
        raise NotImplementedError
    
    def update_repair_part(self, repair_part_id: int, **kwargs) -> Optional[RepairPart]:
        raise NotImplementedError
    
    def delete_repair_part(self, repair_part_id: int) -> bool:
        raise NotImplementedError