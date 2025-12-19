from typing import Optional, List
from models.repair_part import RepairPart
from models.ticket import Ticket
from models.part import Part
from models.user import User
from models.technician import Technician
from interfaces.irepair_part_service import IRepairPartService
from dtos.repair_part_dto import RepairPartDTO

from PySide6.QtCore import QObject, Signal

class RepairPartController(QObject):
    repair_part_changed = Signal()

    def __init__(self, repair_part_service: IRepairPartService):
        super().__init__()
        self._service = repair_part_service

    def create_repair_part(
        self,
        ticket_id: int,
        part_id: int,
        technician_id: Optional[int],
        current_user: Optional[User] = None,
        quantity: int = 1,
        notes: Optional[str] = None
    ) -> RepairPartDTO:
        """Record a part used in a ticket repair"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        result = self._service.create_repair_part(
            ticket_id=ticket_id,
            part_id=part_id,
            technician_id=technician_id,
            current_user=current_user,
            quantity=quantity,
            notes=notes
        )
        self.repair_part_changed.emit()
        return result

    def get_repair_part(self, repair_part_id: int) -> Optional[RepairPartDTO]:
        """Get a repair part record by ID"""
        return self._service.get_repair_part_by_id(repair_part_id)

    def get_parts_used_in_ticket(self, ticket_id: int) -> List[RepairPartDTO]:
        """Get all parts used in a specific ticket"""
        return self._service.get_parts_used_in_ticket(ticket_id)

    def get_repairs_using_part(self, part_id: int) -> List[RepairPartDTO]:
        """Get all repair records where a specific part was used"""
        return self._service.get_repairs_using_part(part_id)

    def update_repair_part(self, repair_part_id: int, **kwargs) -> Optional[RepairPartDTO]:
        """Update repair part details"""
        if 'quantity' in kwargs and kwargs['quantity'] <= 0:
            raise ValueError("Quantity must be positive")
        result = self._service.update_repair_part(repair_part_id, **kwargs)
        if result:
            self.repair_part_changed.emit()
        return result

    def delete_repair_part(self, repair_part_id: int) -> bool:
        """Remove a repair part record"""
        result = self._service.delete_repair_part(repair_part_id)
        if result:
            self.repair_part_changed.emit()
        return result