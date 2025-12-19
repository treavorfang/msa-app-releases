"""RepairPart Repository - Repair Parts Data Access Layer.

This repository handles all database operations for RepairPart entities.
Tracks parts used in tickets/repairs by technicians.
"""

from typing import Optional, List
from peewee import DoesNotExist
from models.repair_part import RepairPart


class RepairPartRepository:
    """Repository for RepairPart data access operations."""
    
    def create_repair_part(
        self,
        ticket,
        part,
        technician,
        quantity: int = 1,
        notes: Optional[str] = None
    ) -> RepairPart:
        """Record usage of a part in a ticket."""
        return RepairPart.create(
            ticket=ticket,
            part=part,
            technician=technician,
            quantity=quantity,
            notes=notes
        )
    
    def get_repair_part_by_id(self, repair_part_id: int) -> Optional[RepairPart]:
        """Get repair part record by ID."""
        try:
            return RepairPart.get_by_id(repair_part_id)
        except DoesNotExist:
            return None
    
    def get_parts_used_in_ticket(self, ticket_id: int) -> List[RepairPart]:
        """Get all parts used in a specific ticket."""
        return list(
            RepairPart.select()
            .where(RepairPart.ticket == ticket_id)
            .order_by(RepairPart.installed_at.desc())
        )
    
    def get_repairs_using_part(self, part_id: int) -> List[RepairPart]:
        """Get all tickets where a specific part was used."""
        return list(
            RepairPart.select()
            .where(RepairPart.part == part_id)
            .order_by(RepairPart.installed_at.desc())
        )
    
    def update_repair_part(self, repair_part_id: int, **kwargs) -> Optional[RepairPart]:
        """Update a repair part usage record."""
        try:
            repair_part = RepairPart.get_by_id(repair_part_id)
            for key, value in kwargs.items():
                setattr(repair_part, key, value)
            repair_part.save()
            return repair_part
        except DoesNotExist:
            return None
    
    def delete_repair_part(self, repair_part_id: int) -> bool:
        """Delete a repair part usage record."""
        try:
            repair_part = RepairPart.get_by_id(repair_part_id)
            repair_part.delete_instance()
            return True
        except DoesNotExist:
            return False