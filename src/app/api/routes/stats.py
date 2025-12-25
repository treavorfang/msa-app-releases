from fastapi import APIRouter
from datetime import datetime
from services.ticket_service import TicketService
from services.audit_service import AuditService

from repositories.part_repository import PartRepository

router = APIRouter()
audit_service = AuditService()
ticket_service = TicketService(audit_service)
part_repo = PartRepository()

@router.get("/summary")
async def get_summary_stats():
    """Get high-level summary statistics via Service (Desktop Parity)."""
    # Use central service for stats calculation
    stats = ticket_service.get_dashboard_stats()
    
    return {
        "active_tickets": stats["in_progress"],
        "urgent_tickets": stats["urgent_tickets"],
        "pending_parts": stats["pending_parts"],
        "ready_pickup": stats["ready_pickup"],
        "returned_today": stats["returned_today"],
        "revenue_today": stats["revenue"],
        "low_stock_count": len(part_repo.get_low_stock_parts()),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/weekly")
async def get_weekly_stats():
    """Get 7-day financial snapshot for Staff dashboard."""
    try:
        from datetime import timedelta
        from models.ticket import Ticket
        from models.repair_part import RepairPart
        from models.part import Part
        from peewee import fn
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Weekly Revenue (Completed tickets)
        revenue_query = Ticket.select(
            fn.strftime('%Y-%m-%d', Ticket.completed_at).alias('day'),
            fn.SUM(Ticket.actual_cost).alias('total')
        ).where(
            (Ticket.status == 'completed') &
            (Ticket.completed_at >= start_date) &
            (Ticket.is_deleted == False)
        ).group_by(fn.strftime('%Y-%m-%d', Ticket.completed_at))
        
        # Weekly Expenses (Parts used in tickets)
        expense_query = RepairPart.select(
            fn.strftime('%Y-%m-%d', RepairPart.installed_at).alias('day'),
            fn.SUM(Part.cost_price * RepairPart.quantity).alias('total')
        ).join(Part).where(
            (RepairPart.installed_at >= start_date)
        ).group_by(fn.strftime('%Y-%m-%d', RepairPart.installed_at))
        
        def get_day_name(day_val):
            if not day_val: return None
            if isinstance(day_val, str):
                try:
                    return datetime.strptime(day_val, '%Y-%m-%d').strftime("%a")
                except ValueError:
                    return day_val[:10] # Fallback
            return day_val.strftime("%a")

        revenue_data = {get_day_name(item.day): float(item.total or 0.0) for item in list(revenue_query) if item.day}
        expense_data = {get_day_name(item.day): float(item.total or 0.0) for item in list(expense_query) if item.day}
        
        # Ensure all 7 days are present
        days = []
        for i in range(7):
            d = (start_date + timedelta(days=i)).strftime("%a")
            days.append({
                "day": d,
                "revenue": revenue_data.get(d, 0.0),
                "expense": expense_data.get(d, 0.0)
            })
            
        return {
            "days": days,
            "total_revenue": sum(revenue_data.values()),
            "total_expense": sum(expense_data.values())
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}
@router.get("/tech/{tech_id}")
async def get_tech_performance(tech_id: int):
    """
    Get performance metrics for a specific technician.
    - Jobs Completed (Today, Week, Month)
    - Average Repair Time (This Week)
    - Pending Jobs Count
    """
    try:
        from models.ticket import Ticket
        from models.work_log import WorkLog
        from peewee import fn
        
        today = datetime.now().date()
        week_start = today - datetime.timedelta(days=7)
        month_start = today - datetime.timedelta(days=30)
        
        # 1. Completed Counts
        completed_base = Ticket.select().where(
            (Ticket.assigned_technician == tech_id) & 
            (Ticket.status == 'completed')
        )
        
        completed_today = completed_base.where(fn.DATE(Ticket.completed_at) == today).count()
        completed_week = completed_base.where(fn.DATE(Ticket.completed_at) >= week_start).count()
        completed_month = completed_base.where(fn.DATE(Ticket.completed_at) >= month_start).count()
        
        # 2. Currently Active
        active_count = Ticket.select().where(
            (Ticket.assigned_technician == tech_id) & 
            (Ticket.status.in_(['in_progress', 'awaiting_parts', 'diagnosed', 'repairing']))
        ).count()
        
        # 3. Efficiency (Avg hours per completed ticket this week)
        # Using WorkLogs if available, otherwise Ticket created vs completed diff
        # Let's use generic created->completed for now as WorkLogs might be sparse
        avg_time_str = "N/A"
        recent_completed = list(completed_base.where(fn.DATE(Ticket.completed_at) >= week_start))
        
        if recent_completed:
            total_seconds = 0
            count = 0
            for t in recent_completed:
                if t.created_at and t.completed_at:
                    delta = (t.completed_at - t.created_at).total_seconds()
                    if delta > 0:
                        total_seconds += delta
                        count += 1
            
            if count > 0:
                avg_hours = round(total_seconds / 3600, 1)
                avg_time_str = f"{avg_hours} hrs"
        
        return {
            "completed_today": completed_today,
            "completed_week": completed_week,
            "completed_month": completed_month,
            "active_tickets": active_count,
            "avg_repair_time": avg_time_str
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}
