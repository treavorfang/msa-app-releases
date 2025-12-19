"""PriceHistory Repository - Price Tracking Data Access Layer.

This repository handles all database operations for PriceHistory entities.
Tracks price changes over time for parts.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from peewee import DoesNotExist
from models.price_history import PriceHistory


class PriceHistoryRepository:
    """Repository for PriceHistory data access operations."""
    
    def create_price_history_entry(self, part_id: int, old_price: float, new_price: float, 
                                   changed_by_id: Optional[int] = None, 
                                   change_reason: Optional[str] = None) -> PriceHistory:
        """Create a new price history entry."""
        return PriceHistory.create(
            part=part_id,
            old_price=old_price,
            new_price=new_price,
            changed_by=changed_by_id,
            change_reason=change_reason
        )
    
    def get_history_for_part(self, part_id: int, limit: int = 100) -> List[PriceHistory]:
        """Get price history for a specific part, ordered by most recent first."""
        return list(
            PriceHistory.select()
            .where(PriceHistory.part == part_id)
            .order_by(PriceHistory.changed_at.desc())
            .limit(limit)
        )
    
    def get_recent_price_changes(self, days: int = 30, limit: int = 100) -> List[PriceHistory]:
        """Get recent price changes across all parts."""
        cutoff_date = datetime.now() - timedelta(days=days)
        return list(
            PriceHistory.select()
            .where(PriceHistory.changed_at >= cutoff_date)
            .order_by(PriceHistory.changed_at.desc())
            .limit(limit)
        )
    
    def get_latest_price_change(self, part_id: int) -> Optional[PriceHistory]:
        """Get the most recent price change for a part."""
        try:
            return (PriceHistory.select()
                   .where(PriceHistory.part == part_id)
                   .order_by(PriceHistory.changed_at.desc())
                   .get())
        except DoesNotExist:
            return None
