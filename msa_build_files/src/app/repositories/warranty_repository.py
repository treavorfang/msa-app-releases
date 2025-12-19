"""Warranty Repository - Warranty Data Access Layer.

This repository handles all database operations for Warranty entities.
Features include warranty creation, tracking, and expiration monitoring.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from models.warranty import Warranty


class WarrantyRepository:
    """Repository for Warranty data access operations."""
    
    def create(self, warranty_data: dict) -> Warranty:
        """Create a new warranty record."""
        return Warranty.create(**warranty_data)
    
    def get(self, warranty_id: int) -> Optional[Warranty]:
        """Get warranty by ID."""
        try:
            return Warranty.get_by_id(warranty_id)
        except Warranty.DoesNotExist:
            return None
    
    def update(self, warranty_id: int, update_data: dict) -> Optional[Warranty]:
        """Update warranty details."""
        try:
            warranty = Warranty.get_by_id(warranty_id)
            for key, value in update_data.items():
                setattr(warranty, key, value)
            warranty.save()
            return warranty
        except Warranty.DoesNotExist:
            return None
    
    def delete(self, warranty_id: int) -> bool:
        """Delete warranty by ID."""
        try:
            warranty = Warranty.get_by_id(warranty_id)
            warranty.delete_instance()
            return True
        except Warranty.DoesNotExist:
            return False
    
    def get_for_item(self, item_type: str, item_id: int) -> List[Warranty]:
        """Get all warranties for a specific item (polymorphic)."""
        return list(Warranty.select().where(
            (Warranty.warrantyable_type == item_type) &
            (Warranty.warrantyable_id == item_id)
        ))
    
    def get_expiring_soon(self, days: int = 30) -> List[Warranty]:
        """Get active warranties expiring within the specified number of days."""
        threshold_date = datetime.now() + timedelta(days=days)
        return list(Warranty.select().where(
            (Warranty.end_date <= threshold_date) &
            (Warranty.end_date >= datetime.now()) &
            (Warranty.status == 'active')
        ))