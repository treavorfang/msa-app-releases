# src/app/controllers/technician_bonus_controller.py
"""
Technician Bonus Controller

Handles all bonus-related operations:
- Creating bonuses
- Listing bonuses
- Calculating auto-bonuses based on performance
- Managing bonus payments
"""

from models.technician_bonus import TechnicianBonus
from models.technician import Technician
from models.technician_performance import TechnicianPerformance
from decimal import Decimal
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from PySide6.QtCore import QObject, Signal


class TechnicianBonusController(QObject):
    """Controller for managing technician bonuses"""
    
    bonus_created = Signal()
    bonus_updated = Signal()
    bonus_paid = Signal()
    
    def __init__(self):
        super().__init__()
    
    def create_bonus(self, technician_id: int, bonus_type: str, amount: Decimal,
                    reason: str = None, period_start: date = None, period_end: date = None,
                    user_id: int = None) -> TechnicianBonus:
        """Create a new bonus for a technician"""
        bonus = TechnicianBonus.create(
            technician=technician_id,
            bonus_type=bonus_type,
            amount=amount,
            reason=reason,
            period_start=period_start,
            period_end=period_end,
            created_by=user_id
        )
        
        self.bonus_created.emit()
        return bonus
    
    def list_bonuses(self, technician_id: int = None, bonus_type: str = None,
                    paid: bool = None, start_date: date = None, end_date: date = None):
        """List bonuses with optional filters"""
        query = TechnicianBonus.select()
        
        if technician_id:
            query = query.where(TechnicianBonus.technician == technician_id)
        
        if bonus_type:
            query = query.where(TechnicianBonus.bonus_type == bonus_type)
        
        if paid is not None:
            query = query.where(TechnicianBonus.paid == paid)
        
        if start_date:
            query = query.where(TechnicianBonus.awarded_date >= start_date)
        
        if end_date:
            query = query.where(TechnicianBonus.awarded_date <= end_date)
        
        return list(query.order_by(TechnicianBonus.awarded_date.desc()))
    
    def mark_as_paid(self, bonus_id: int) -> bool:
        """Mark a bonus as paid"""
        try:
            bonus = TechnicianBonus.get_by_id(bonus_id)
            bonus.paid = True
            bonus.paid_date = datetime.now()
            bonus.save()
            
            self.bonus_paid.emit()
            return True
        except:
            return False
    
    def calculate_performance_bonus(self, technician_id: int, month: date) -> Decimal:
        """
        Calculate performance bonus based on tickets completed
        
        Thresholds:
        - 20+ tickets: $500
        - 15-19 tickets: $300
        - 10-14 tickets: $150
        """
        try:
            perf = TechnicianPerformance.get(
                (TechnicianPerformance.technician == technician_id) &
                (TechnicianPerformance.month == month)
            )
            
            tickets = perf.tickets_completed
            
            if tickets >= 20:
                return Decimal('500.00')
            elif tickets >= 15:
                return Decimal('300.00')
            elif tickets >= 10:
                return Decimal('150.00')
            else:
                return Decimal('0.00')
        except:
            return Decimal('0.00')
    
    def calculate_quality_bonus(self, technician_id: int, month: date) -> Decimal:
        """
        Calculate quality bonus based on customer ratings
        
        Thresholds:
        - 4.5+ rating: $300
        - 4.0-4.49 rating: $150
        """
        try:
            perf = TechnicianPerformance.get(
                (TechnicianPerformance.technician == technician_id) &
                (TechnicianPerformance.month == month)
            )
            
            rating = float(perf.avg_customer_rating)
            
            if rating >= 4.5:
                return Decimal('300.00')
            elif rating >= 4.0:
                return Decimal('150.00')
            else:
                return Decimal('0.00')
        except:
            return Decimal('0.00')
    
    def calculate_revenue_bonus(self, technician_id: int, month: date, target: Decimal = Decimal('10000.00')) -> Decimal:
        """
        Calculate revenue bonus based on revenue above target
        
        Formula: 5% of revenue above target
        """
        try:
            perf = TechnicianPerformance.get(
                (TechnicianPerformance.technician == technician_id) &
                (TechnicianPerformance.month == month)
            )
            
            revenue = perf.revenue_generated
            
            if revenue > target:
                excess = revenue - target
                return excess * Decimal('0.05')  # 5% of excess
            else:
                return Decimal('0.00')
        except:
            return Decimal('0.00')
    
    def auto_calculate_bonuses(self, technician_id: int, month: date, user_id: int = None):
        """
        Automatically calculate and create bonuses for a technician for a given month
        """
        bonuses_created = []
        
        # Performance bonus
        perf_bonus = self.calculate_performance_bonus(technician_id, month)
        if perf_bonus > 0:
            bonus = self.create_bonus(
                technician_id=technician_id,
                bonus_type='performance',
                amount=perf_bonus,
                reason=f"Performance bonus for {month.strftime('%B %Y')}",
                period_start=month,
                period_end=month + relativedelta(months=1, days=-1),
                user_id=user_id
            )
            bonuses_created.append(bonus)
        
        # Quality bonus
        quality_bonus = self.calculate_quality_bonus(technician_id, month)
        if quality_bonus > 0:
            bonus = self.create_bonus(
                technician_id=technician_id,
                bonus_type='quality',
                amount=quality_bonus,
                reason=f"Quality bonus for {month.strftime('%B %Y')}",
                period_start=month,
                period_end=month + relativedelta(months=1, days=-1),
                user_id=user_id
            )
            bonuses_created.append(bonus)
        
        # Revenue bonus
        revenue_bonus = self.calculate_revenue_bonus(technician_id, month)
        if revenue_bonus > 0:
            bonus = self.create_bonus(
                technician_id=technician_id,
                bonus_type='revenue',
                amount=revenue_bonus,
                reason=f"Revenue bonus for {month.strftime('%B %Y')}",
                period_start=month,
                period_end=month + relativedelta(months=1, days=-1),
                user_id=user_id
            )
            bonuses_created.append(bonus)
        
        return bonuses_created
    
    def get_total_bonuses(self, technician_id: int, start_date: date = None, end_date: date = None) -> Decimal:
        """Get total bonus amount for a technician"""
        query = TechnicianBonus.select().where(TechnicianBonus.technician == technician_id)
        
        if start_date:
            query = query.where(TechnicianBonus.awarded_date >= start_date)
        
        if end_date:
            query = query.where(TechnicianBonus.awarded_date <= end_date)
        
        total = sum(Decimal(str(bonus.amount)) for bonus in query)
        return total
    
    def get_unpaid_bonuses_total(self, technician_id: int) -> Decimal:
        """Get total unpaid bonuses for a technician"""
        query = TechnicianBonus.select().where(
            (TechnicianBonus.technician == technician_id) &
            (TechnicianBonus.paid == False)
        )
        
        total = sum(Decimal(str(bonus.amount)) for bonus in query)
        return total
