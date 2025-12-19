"""Technician Repository - Technician Data Access Layer.

This repository handles all database operations for Technician entities.
Features include technician management, search, and status tracking.
"""

from typing import Optional, List
from peewee import fn
from models.technician import Technician


class TechnicianRepository:
    """Repository for Technician data access operations."""
    
    def create(self, technician_data: dict) -> Technician:
        """Create a new technician."""
        return Technician.create(**technician_data)
    
    def get(self, technician_id: int) -> Optional[Technician]:
        """Get technician by ID."""
        try:
            return Technician.get_by_id(technician_id)
        except Technician.DoesNotExist:
            return None
    
    def get_by_user(self, user_id: int) -> Optional[Technician]:
        """Get technician by associated user ID."""
        # Note: This method was marked for removal/redesign in original file
        # Keeping it for interface compatibility, returning None as per original
        return None
    
    def update(self, technician_id: int, update_data: dict) -> Optional[Technician]:
        """Update technician details."""
        try:
            technician = Technician.get_by_id(technician_id)
            for key, value in update_data.items():
                setattr(technician, key, value)
            technician.save()
            return technician
        except Technician.DoesNotExist:
            return None
    
    def deactivate(self, technician_id: int) -> bool:
        """Deactivate a technician (soft delete/inactive status)."""
        try:
            technician = Technician.get_by_id(technician_id)
            technician.is_active = False
            technician.save()
            return True
        except Technician.DoesNotExist:
            return False
    
    def list_all(self, active_only: bool = True) -> List[Technician]:
        """Get all technicians, optionally filtering for active only."""
        query = Technician.select()
        if active_only:
            query = query.where(Technician.is_active == True)
        return list(query)
    
    def search(self, search_term: str) -> List[Technician]:
        """Search technicians by name, certification, specialization, or email."""
        search_term = search_term.lower()
        return list(Technician.select().where(
            (fn.LOWER(Technician.full_name).contains(search_term)) |
            (fn.LOWER(Technician.certification).contains(search_term)) |
            (fn.LOWER(Technician.specialization).contains(search_term)) |
            (fn.LOWER(Technician.email).contains(search_term))
        ))