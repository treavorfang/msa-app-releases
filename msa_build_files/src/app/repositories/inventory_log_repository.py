"""InventoryLog Repository - Inventory Logging Data Access Layer.

This repository handles all database operations for InventoryLog entities.
Tracks movement and changes in inventory.
"""

from typing import List
from models.inventory_log import InventoryLog


class InventoryLogRepository:
    """Repository for InventoryLog data access operations."""
    
    def create_log(self, log_data: dict) -> InventoryLog:
        """Create a new inventory log entry."""
        return InventoryLog.create(**log_data)
    
    def get_logs_for_part(self, part_id: int, limit: int = 100) -> List[InventoryLog]:
        """Get inventory logs for a specific part."""
        return list(InventoryLog.select()
                          .where(InventoryLog.part == part_id)
                          .order_by(InventoryLog.logged_at.desc())
                          .limit(limit))
    
    def get_logs_for_reference(self, reference_type: str, reference_id: int) -> List[InventoryLog]:
        """Get inventory logs by reference (e.g. ticket, purchase order)."""
        return list(InventoryLog.select()
                          .where(
                              (InventoryLog.reference_type == reference_type) &
                              (InventoryLog.reference_id == reference_id)
                          )
                          .order_by(InventoryLog.logged_at))