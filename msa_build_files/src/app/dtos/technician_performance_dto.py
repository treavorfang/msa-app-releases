"""TechnicianPerformance DTO - Data Transfer Object."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass
class TechnicianPerformanceDTO:
    """Data Transfer Object for TechnicianPerformance."""
    
    id: Optional[int] = None
    technician_id: Optional[int] = None
    month: Optional[date] = None
    tickets_completed: int = 0
    tickets_pending: int = 0
    avg_completion_days: Decimal = Decimal("0.00")
    avg_customer_rating: Decimal = Decimal("0.00")
    total_ratings: int = 0
    revenue_generated: Decimal = Decimal("0.00")
    commission_earned: Decimal = Decimal("0.00")
    bonuses_earned: Decimal = Decimal("0.00")
    efficiency_score: Decimal = Decimal("0.00")
    updated_at: Optional[datetime] = None
    
    # Flattened
    technician_name: Optional[str] = None

    @classmethod
    def from_model(cls, perf) -> 'TechnicianPerformanceDTO':
        """Convert model to DTO."""
        dto = cls(
            id=perf.id,
            technician_id=perf.technician_id if perf.technician else None,
            month=perf.month,
            tickets_completed=perf.tickets_completed,
            tickets_pending=perf.tickets_pending,
            avg_completion_days=perf.avg_completion_days,
            avg_customer_rating=perf.avg_customer_rating,
            total_ratings=perf.total_ratings,
            revenue_generated=perf.revenue_generated,
            commission_earned=perf.commission_earned,
            bonuses_earned=perf.bonuses_earned,
            efficiency_score=perf.efficiency_score,
            updated_at=perf.updated_at,
            technician_name=perf.technician.full_name if perf.technician else None
        )
        return dto
    
    def to_dict(self) -> dict:
        """Convert key metrics to dict."""
        return {
            'technician_id': self.technician_id,
            'technician_name': self.technician_name,
            'tickets_completed': self.tickets_completed,
            'revenue_generated': float(self.revenue_generated),
            'commission_earned': float(self.commission_earned),
            'efficiency_score': float(self.efficiency_score),
            'avg_completion_days': float(self.avg_completion_days)
        }
