"""TechnicianPerformanceService - Performance Tracking Logic.

This service manages performance metrics and calculations.
"""

from typing import List, Optional, Any, Dict
from datetime import datetime, date
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from interfaces.itechnician_performance_service import ITechnicianPerformanceService
from dtos.technician_performance_dto import TechnicianPerformanceDTO
from models.technician_performance import TechnicianPerformance
from models.technician import Technician
from models.ticket import Ticket
from models.technician_bonus import TechnicianBonus


class TechnicianPerformanceService(ITechnicianPerformanceService):
    """Service class for Performance operations."""
    
    def calculate_monthly_performance(self, technician_id: int, month: date) -> TechnicianPerformanceDTO:
        """Calculate and save performance metrics."""
        # Ensure month is first day of month
        month = date(month.year, month.month, 1)
        
        # Calculate date range
        month_start = datetime(month.year, month.month, 1)
        month_end = month_start + relativedelta(months=1)
        
        # Get or create performance record
        try:
            perf = TechnicianPerformance.get(
                (TechnicianPerformance.technician == technician_id) &
                (TechnicianPerformance.month == month)
            )
        except TechnicianPerformance.DoesNotExist:
            perf = TechnicianPerformance.create(
                technician=technician_id,
                month=month
            )
        
        # Calculate ticket metrics
        tickets = Ticket.select().where(
            (Ticket.assigned_technician == technician_id) &
            (Ticket.created_at >= month_start) &
            (Ticket.created_at < month_end)
        )
        
        completed_tickets = [t for t in tickets if t.status == 'completed']
        pending_tickets = [t for t in tickets if t.status in ['open', 'in_progress']]
        
        perf.tickets_completed = len(completed_tickets)
        perf.tickets_pending = len(pending_tickets)
        
        # Calculate average completion time
        if completed_tickets:
            completion_times = []
            for ticket in completed_tickets:
                if ticket.completed_at and ticket.created_at:
                    days = (ticket.completed_at - ticket.created_at).days
                    completion_times.append(days)
            
            if completion_times:
                perf.avg_completion_days = Decimal(str(sum(completion_times) / len(completion_times)))
        
        # Placeholder for ratings
        perf.avg_customer_rating = Decimal('0.00')
        perf.total_ratings = 0
        
        # Calculate revenue generated
        revenue = Decimal('0.00')
        for ticket in completed_tickets:
            if hasattr(ticket, 'total_cost') and ticket.total_cost:
                revenue += Decimal(str(ticket.total_cost))
        
        perf.revenue_generated = revenue
        
        # Calculate commission earned
        technician = Technician.get_by_id(technician_id)
        commission_rate = Decimal(str(technician.commission_rate or 0)) / Decimal('100')
        perf.commission_earned = revenue * commission_rate
        
        # Calculate bonuses
        bonuses = TechnicianBonus.select().where(
            (TechnicianBonus.technician == technician_id) &
            (TechnicianBonus.period_start >= month) &
            (TechnicianBonus.period_start < month_end)
        )
        perf.bonuses_earned = sum(Decimal(str(b.amount)) for b in bonuses)
        
        # Calculate efficiency score (tickets per day worked, assuming 22 days)
        if perf.tickets_completed > 0:
            perf.efficiency_score = Decimal(str(perf.tickets_completed / 22.0))
        else:
            perf.efficiency_score = Decimal('0.00')
        
        # Update timestamp
        perf.updated_at = datetime.now()
        perf.save()
        
        return TechnicianPerformanceDTO.from_model(perf)
    
    def get_performance(self, technician_id: int, month: date) -> TechnicianPerformanceDTO:
        """Get performance record for a specific month."""
        month = date(month.year, month.month, 1)
        
        try:
            perf = TechnicianPerformance.get(
                (TechnicianPerformance.technician == technician_id) &
                (TechnicianPerformance.month == month)
            )
            return TechnicianPerformanceDTO.from_model(perf)
        except TechnicianPerformance.DoesNotExist:
            return self.calculate_monthly_performance(technician_id, month)
    
    def get_performance_history(self, technician_id: int, months: int = 12) -> List[TechnicianPerformanceDTO]:
        """Get performance history for last N months."""
        records = TechnicianPerformance.select().where(
            TechnicianPerformance.technician == technician_id
        ).order_by(TechnicianPerformance.month.desc()).limit(months)
        
        return [TechnicianPerformanceDTO.from_model(r) for r in records]
    
    def get_year_to_date_summary(self, technician_id: int) -> Dict[str, Any]:
        """Get year-to-date performance summary."""
        year_start = date(datetime.now().year, 1, 1)
        
        records = TechnicianPerformance.select().where(
            (TechnicianPerformance.technician == technician_id) &
            (TechnicianPerformance.month >= year_start)
        )
        records_list = list(records)
        
        summary = {
            'total_tickets': sum(r.tickets_completed for r in records_list),
            'total_revenue': sum(Decimal(str(r.revenue_generated)) for r in records_list),
            'total_commission': sum(Decimal(str(r.commission_earned)) for r in records_list),
            'total_bonuses': sum(Decimal(str(r.bonuses_earned)) for r in records_list),
            'avg_completion_days': Decimal('0.00'),
            'avg_efficiency': Decimal('0.00'),
            'months_tracked': len(records_list)
        }
        
        if summary['months_tracked'] > 0:
            summary['avg_completion_days'] = sum(
                Decimal(str(r.avg_completion_days)) for r in records_list
            ) / summary['months_tracked']
            
            summary['avg_efficiency'] = sum(
                Decimal(str(r.efficiency_score)) for r in records_list
            ) / summary['months_tracked']
        
        # Convert Decimals to float for JSON compatibility if needed, keeping Decimal here for consistency.
        return summary
    
    def recalculate_all_months(self, technician_id: int, start_month: Optional[date] = None) -> None:
        """Recalculate performance for all months."""
        if not start_month:
            start_month = date.today() - relativedelta(months=12)
        
        start_month = date(start_month.year, start_month.month, 1)
        current_month = date(datetime.now().year, datetime.now().month, 1)
        
        month = start_month
        while month <= current_month:
            self.calculate_monthly_performance(technician_id, month)
            month = month + relativedelta(months=1)
            
    def get_team_comparison(self, month: Optional[date] = None) -> List[Dict[str, Any]]:
        """Get performance comparison across all technicians."""
        if not month:
            month = date(datetime.now().year, datetime.now().month, 1)
        
        month = date(month.year, month.month, 1)
        
        records = TechnicianPerformance.select().where(
            TechnicianPerformance.month == month
        )
        
        comparison = []
        for record in records:
            dto = TechnicianPerformanceDTO.from_model(record)
            comparison.append(dto.to_dict())
        
        # Sort by tickets completed
        comparison.sort(key=lambda x: x['tickets_completed'], reverse=True)
        
        return comparison
        
    def get_top_performers(self, month: Optional[date] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing technicians."""
        comparison = self.get_team_comparison(month)
        return comparison[:limit]
