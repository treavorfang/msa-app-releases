"""Ticket Repository - Ticket Management Data Access Layer.

This repository handles all database operations for Ticket entities.
It acts as the central hub for service requests, managing lifecycle,
assignments, and reporting statistics.
"""

from typing import Optional, List, Dict
from datetime import datetime
from peewee import JOIN, fn
from models.ticket import Ticket
from models.invoice import Invoice
from models.device import Device
from models.customer import Customer
from models.technician import Technician
from models.branch import Branch


class TicketRepository:
    """Repository for Ticket data access operations."""
    
    def create(self, ticket_data: dict) -> Ticket:
        """Create a new ticket."""
        return Ticket.create(**ticket_data)
    
    def get(self, ticket_id: int, include_deleted: bool = False) -> Optional[Ticket]:
        """Get a ticket by ID with eager loaded relationships."""
        try:
            # Eager load related entities to avoid N+1 queries
            query = (Ticket
                    .select(Ticket, Device, Customer, Technician, Branch)
                    .join(Device, on=(Ticket.device == Device.id))
                    .join(Customer, on=(Device.customer == Customer.id))
                    .switch(Ticket)
                    .join(Technician, on=(Ticket.assigned_technician == Technician.id), join_type=JOIN.LEFT_OUTER)
                    .switch(Ticket)
                    .join(Branch, on=(Ticket.branch == Branch.id), join_type=JOIN.LEFT_OUTER))
            
            if not include_deleted:
                query = query.where(Ticket.is_deleted == False)
                
            return query.where(Ticket.id == ticket_id).get()
        except Ticket.DoesNotExist:
            return None
    
    def update(self, ticket_id: int, update_data: dict) -> Optional[Ticket]:
        """Update a ticket's details."""
        try:
            # Simple retrieval for update - no need for complex joins
            ticket = Ticket.select().where(Ticket.id == ticket_id).first()
            if not ticket:
                return None
            
            for key, value in update_data.items():
                setattr(ticket, key, value)
            ticket.save()
            return ticket
        except Ticket.DoesNotExist:
            return None
    
    def delete(self, ticket_id: int) -> bool:
        """Soft delete a ticket."""
        try:
            ticket = Ticket.select().where(Ticket.id == ticket_id).first()
            if not ticket:
                return False
            
            ticket.is_deleted = True
            ticket.deleted_at = datetime.now()
            ticket.save()
            return True
        except Ticket.DoesNotExist:
            return False
    
    def restore(self, ticket_id: int) -> bool:
        """Restore a soft-deleted ticket."""
        try:
            ticket = Ticket.select().where(Ticket.id == ticket_id).first()
            if not ticket:
                return False
            
            ticket.is_deleted = False
            ticket.deleted_at = None
            ticket.save()
            return True
        except Ticket.DoesNotExist:
            return False
    
    def list_all(self, filters: dict = None) -> List[Ticket]:
        """List tickets with optional filtering."""
        # Eager load relationships
        query = (Ticket
                .select(Ticket, Device, Customer, Technician, Branch)
                .join(Device, on=(Ticket.device == Device.id))
                .join(Customer, on=(Device.customer == Customer.id))
                .switch(Ticket)
                .join(Technician, on=(Ticket.assigned_technician == Technician.id), join_type=JOIN.LEFT_OUTER)
                .switch(Ticket)
                .join(Branch, on=(Ticket.branch == Branch.id), join_type=JOIN.LEFT_OUTER))
        
        # Apply soft delete filter
        include_deleted = filters.get('include_deleted', False) if filters else False
        if not include_deleted:
            query = query.where(Ticket.is_deleted == False)
        
        if filters:
            if 'status' in filters and filters['status']:
                status_filter = filters['status']
                if isinstance(status_filter, (list, tuple)):
                    query = query.where(Ticket.status << status_filter)
                else:
                    query = query.where(Ticket.status == status_filter)
            if 'priority' in filters and filters['priority']:
                query = query.where(Ticket.priority == filters['priority'])
            if 'technician_id' in filters:
                query = query.where(Ticket.assigned_technician == filters['technician_id'])
            if 'customer_id' in filters:
                # Already joined Device, so we can filter on it
                query = query.where(Device.customer == filters['customer_id'])
            if 'branch_id' in filters and filters['branch_id']:
                query = query.where(Ticket.branch == filters['branch_id'])
            if 'exclude_returned' in filters and filters['exclude_returned']:
                query = query.where(Device.status != 'returned')
            if 'only_returned' in filters and filters['only_returned']:
                query = query.where(Device.status == 'returned')
                
        # Apply sorting (default: created_at desc)
        query = query.order_by(Ticket.created_at.desc())
        
        # Apply pagination
        if filters:
            if 'limit' in filters:
                query = query.limit(filters['limit'])
            if 'offset' in filters:
                query = query.offset(filters['offset'])
                
        return list(query)
    
    def search(self, search_term: str, include_deleted: bool = False) -> List[Ticket]:
        """Search tickets by number, error description, IMEI, or Serial."""
        # Use LEFT OUTER JOIN for safety (parity with original select)
        query = (Ticket
                .select(Ticket)
                .join(Device, JOIN.LEFT_OUTER, on=(Ticket.device == Device.id))
                .where(
                    (Ticket.ticket_number.contains(search_term)) |
                    (Ticket.error.contains(search_term)) |
                    (Device.imei == search_term) |
                    (Device.serial_number == search_term)
                ))
        if not include_deleted:
            query = query.where(Ticket.is_deleted == False)
        return list(query)
    def get_dashboard_stats(self, date=None, branch_id: Optional[int] = None) -> dict:
        """Get statistical overview for the dashboard."""
        if not date:
            date = datetime.now().date()
            
        # New jobs today
        new_jobs_query = Ticket.select().where(
            (Ticket.created_at >= datetime.combine(date, datetime.min.time())) &
            (Ticket.created_at <= datetime.combine(date, datetime.max.time())) &
            (Ticket.is_deleted == False)
        )
        if branch_id:
            new_jobs_query = new_jobs_query.where(Ticket.branch == branch_id)
        new_jobs = new_jobs_query.count()
        
        # In progress (total active)
        in_progress_query = Ticket.select().where(
            (Ticket.status << ['in_progress', 'diagnosed', 'awaiting_parts']) &
            (Ticket.is_deleted == False)
        )
        if branch_id:
            in_progress_query = in_progress_query.where(Ticket.branch == branch_id)
        in_progress = in_progress_query.count()
        
        # Completed today
        completed_query = Ticket.select().where(
            (Ticket.status == 'completed') &
            (Ticket.completed_at >= datetime.combine(date, datetime.min.time())) &
            (Ticket.completed_at <= datetime.combine(date, datetime.max.time())) &
            (Ticket.is_deleted == False)
        )
        if branch_id:
            completed_query = completed_query.where(Ticket.branch == branch_id)
        completed = completed_query.count()
        
        # Revenue today
        revenue_query = Ticket.select(fn.SUM(Ticket.estimated_cost)).where(
            (Ticket.status == 'completed') &
            (Ticket.completed_at >= datetime.combine(date, datetime.min.time())) &
            (Ticket.completed_at <= datetime.combine(date, datetime.max.time())) &
            (Ticket.is_deleted == False)
        )
        if branch_id:
            revenue_query = revenue_query.where(Ticket.branch == branch_id)
        revenue = revenue_query.scalar() or 0.0

        # Urgent tickets
        urgent_query = Ticket.select().where(
            (Ticket.priority << ['high', 'critical', 'urgent']) &
            (Ticket.status != 'completed') &
            (Ticket.is_deleted == False)
        )
        if branch_id:
            urgent_query = urgent_query.where(Ticket.branch == branch_id)
        urgent_count = urgent_query.count()
        
        # Awaiting parts
        waiting_query = Ticket.select().where(
            (Ticket.status == 'awaiting_parts') &
            (Ticket.is_deleted == False)
        )
        if branch_id:
            waiting_query = waiting_query.where(Ticket.branch == branch_id)
        pending_parts = waiting_query.count()

        # Returned Today (Devices)
        returned_today_query = Device.select().where(
            (Device.status == 'returned') &
            (Device.updated_at >= datetime.combine(date, datetime.min.time())) &
            (Device.is_deleted == False)
        )
        if branch_id:
            returned_today_query = returned_today_query.where(Device.branch == branch_id)
        returned_today = returned_today_query.count()

        return {
            "new_jobs": new_jobs,
            "in_progress": in_progress,
            "completed": completed,
            "revenue": float(revenue),
            "urgent_tickets": urgent_count,
            "pending_parts": pending_parts,
            "ready_pickup": completed,
            "returned_today": returned_today
        }
    
    def get_recent(self, limit: int = 10, branch_id: Optional[int] = None) -> List[Ticket]:
        """Get most recent tickets."""
        query = Ticket.select().where(Ticket.is_deleted == False).order_by(Ticket.created_at.desc())
        if branch_id:
            query = query.where(Ticket.branch == branch_id)
        return list(query.limit(limit))
    
    def get_dashboard_stats_range(self, start_date, end_date, branch_id: Optional[int] = None) -> dict:
        """Get statistics for a specific date range."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # New jobs in range
        new_jobs_query = Ticket.select().where(
            (Ticket.created_at >= start_datetime) &
            (Ticket.created_at <= end_datetime) &
            (Ticket.is_deleted == False)
        )
        if branch_id:
            new_jobs_query = new_jobs_query.where(Ticket.branch == branch_id)
        new_jobs = new_jobs_query.count()
        
        # In progress (total active - not date specific)
        in_progress_query = Ticket.select().where(
            (Ticket.status << ['in_progress', 'diagnosed', 'awaiting_parts']) &
            (Ticket.is_deleted == False)
        )
        if branch_id:
            in_progress_query = in_progress_query.where(Ticket.branch == branch_id)
        in_progress = in_progress_query.count()
        
        # Completed in range
        completed_query = Ticket.select().where(
            (Ticket.status == 'completed') &
            (Ticket.completed_at >= start_datetime) &
            (Ticket.completed_at <= end_datetime) &
            (Ticket.is_deleted == False)
        )
        if branch_id:
            completed_query = completed_query.where(Ticket.branch == branch_id)
        completed = completed_query.count()
        
        # Revenue in range
        revenue_query = Invoice.select(fn.SUM(Invoice.total)).where(
            (Invoice.created_at >= start_datetime) &
            (Invoice.created_at <= end_datetime)
        )
        if branch_id:
            revenue_query = revenue_query.where(Invoice.branch == branch_id)
        
        revenue = revenue_query.scalar() or 0.0
        
        # Total tickets in range
        total_tickets_query = Ticket.select().where(
            (Ticket.created_at >= start_datetime) &
            (Ticket.created_at <= end_datetime) &
            (Ticket.is_deleted == False)
        )
        if branch_id:
            total_tickets_query = total_tickets_query.where(Ticket.branch == branch_id)
        total_tickets = total_tickets_query.count()
        
        # Completion rate
        completion_rate = (completed / total_tickets * 100) if total_tickets > 0 else 0.0
        
        # Active technicians (technicians with active tickets)
        active_techs_query = Ticket.select(Ticket.assigned_technician).where(
            (Ticket.status << ['in_progress', 'diagnosed', 'awaiting_parts']) &
            (Ticket.is_deleted == False) &
            (Ticket.assigned_technician.is_null(False))
        )
        if branch_id:
            active_techs_query = active_techs_query.where(Ticket.branch == branch_id)
        active_technicians = active_techs_query.distinct().count()
        
        return {
            "new_jobs": new_jobs,
            "in_progress": in_progress,
            "completed": completed,
            "revenue": float(revenue),
            "total_tickets": total_tickets,
            "completion_rate": round(completion_rate, 2),
            "active_technicians": active_technicians
        }
    
    def get_technician_performance(self, start_date, end_date, branch_id: Optional[int] = None) -> List[dict]:
        """Get performance statistics for each technician."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        technicians = []
        
        # Get all unique technicians who have tickets
        tech_ids_query = (Ticket
            .select(Ticket.assigned_technician)
            .where(
                (Ticket.is_deleted == False) &
                (Ticket.assigned_technician.is_null(False))
            )
            .distinct()
        )
        if branch_id:
            tech_ids_query = tech_ids_query.where(Ticket.branch == branch_id)
        
        for tech_ticket in tech_ids_query:
            tech_id = tech_ticket.assigned_technician.id
            tech = Technician.get_by_id(tech_id)
            
            # Count total assigned tickets
            assigned_query = Ticket.select().where(
                (Ticket.assigned_technician == tech_id) &
                (Ticket.is_deleted == False)
            )
            if branch_id:
                assigned_query = assigned_query.where(Ticket.branch == branch_id)
            total_assigned = assigned_query.count()
            
            # Count completed tickets in date range
            completed_count_query = Ticket.select().where(
                (Ticket.assigned_technician == tech_id) &
                (Ticket.status == 'completed') &
                (Ticket.completed_at >= start_datetime) &
                (Ticket.completed_at <= end_datetime) &
                (Ticket.is_deleted == False)
            )
            if branch_id:
                completed_count_query = completed_count_query.where(Ticket.branch == branch_id)
            completed_count = completed_count_query.count()
            
            # Sum revenue from completed tickets in date range
            completed_tickets_query = Ticket.select().where(
                (Ticket.assigned_technician == tech_id) &
                (Ticket.status == 'completed') &
                (Ticket.completed_at >= start_datetime) &
                (Ticket.completed_at <= end_datetime) &
                (Ticket.is_deleted == False)
            )
            if branch_id:
                completed_tickets_query = completed_tickets_query.where(Ticket.branch == branch_id)
            
            revenue = 0.0
            for ticket in completed_tickets_query:
                # Use actual_cost if set (from invoice), otherwise use estimated_cost
                cost = float(ticket.actual_cost) if ticket.actual_cost > 0 else float(ticket.estimated_cost or 0.0)
                revenue += cost
            
            technicians.append({
                'technician_id': tech_id,
                'technician_name': tech.full_name,
                'total_assigned': total_assigned,
                'tickets_completed': completed_count,
                'total_revenue': float(revenue)
            })
        
        return technicians
    
    def get_status_distribution(self, start_date, end_date) -> dict:
        """Get distribution of ticket statuses for date range."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Get count for each status
        status_query = (Ticket
            .select(Ticket.status, fn.COUNT(Ticket.id).alias('count'))
            .where(
                (Ticket.created_at >= start_datetime) &
                (Ticket.created_at <= end_datetime) &
                (Ticket.is_deleted == False)
            )
            .group_by(Ticket.status)
        )
        
        distribution = {}
        for item in status_query:
            distribution[item.status] = item.count
        
        return distribution
    
    def get_revenue_trend(self, start_date, end_date, branch_id: Optional[int] = None) -> List[dict]:
        """Get daily revenue for the date range using actual Invoices."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Query Invoices directly
        trend_query = (Invoice
            .select(
                fn.DATE(Invoice.created_at).alias('date'),
                fn.SUM(Invoice.total).alias('revenue'),
                fn.COUNT(Invoice.id).alias('count')
            )
            .where(
                (Invoice.created_at >= start_datetime) &
                (Invoice.created_at <= end_datetime)
            )
        )
        
        if branch_id:
            trend_query = trend_query.where(Invoice.branch == branch_id)
            
        trend_query = trend_query.group_by(fn.DATE(Invoice.created_at)).order_by(fn.DATE(Invoice.created_at))
        
        trend = []
        for item in trend_query:
            trend.append({
                'date': str(item.date).split(" ")[0],
                'revenue': float(item.revenue or 0.0),
                'count': item.count
            })
        
        return trend
    
    def get_average_completion_time(self, start_date, end_date, branch_id: Optional[int] = None) -> float:
        """Get average time (in hours) to complete tickets."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Get completed tickets with both created_at and completed_at
        query = Ticket.select().where(
            (Ticket.status == 'completed') &
            (Ticket.completed_at >= start_datetime) &
            (Ticket.completed_at <= end_datetime) &
            (Ticket.is_deleted == False) &
            (Ticket.completed_at.is_null(False))
        )
        if branch_id:
            query = query.where(Ticket.branch == branch_id)
            
        completed_tickets = list(query)
        
        if not completed_tickets:
            return 0.0
        
        total_hours = 0
        count = 0
        
        for ticket in completed_tickets:
            if ticket.created_at and ticket.completed_at:
                time_diff = ticket.completed_at - ticket.created_at
                hours = time_diff.total_seconds() / 3600
                total_hours += hours
                count += 1
        
        return round(total_hours / count, 2) if count > 0 else 0.0