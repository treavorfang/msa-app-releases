"""ReportService - Business Intelligence and Reporting Logic.

This service aggregates data to generate various business reports including:
- Ticket Performance (Daily summaries, Technician stats)
- Financials (Revenue, Profit, Invoices)
- Inventory (Stock levels, Movement)
- CRM (Customer activity)
- Supply Chain (Supplier performance)
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
from peewee import fn, Case

from models.ticket import Ticket
from models.technician import Technician
from models.customer import Customer
from models.invoice import Invoice
from models.part import Part
from models.repair_part import RepairPart
from models.device import Device
from models.work_log import WorkLog
from models.purchase_order import PurchaseOrder
from models.purchase_order_item import PurchaseOrderItem
from models.supplier import Supplier


class ReportService:
    """Service class for generating system reports."""
    
    def __init__(self):
        """Initialize ReportService."""
        pass
    
    # ==================== TICKET REPORTS ====================
    
    def get_daily_ticket_summary(self, start_date: date, end_date: date, branch_id: Optional[int] = None) -> List[Dict]:
        """Generate daily ticket summary report.
        
        Returns:
            List of daily stats: new tickets, completed, in-progress, revenue, parts used.
        """
        # Convert dates to datetime for comparison
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Query for daily aggregates
        query = Ticket.select(
                fn.DATE(Ticket.created_at).alias('date'),
                fn.COUNT(Ticket.id).alias('new_tickets'),
                fn.SUM(Case(None, [(Ticket.status == 'completed', 1)], 0)).alias('completed'),
                fn.SUM(Case(None, [(Ticket.status == 'in_progress', 1)], 0)).alias('in_progress'),
                fn.SUM(Ticket.estimated_cost).alias('total_revenue')
            ).where(
                (Ticket.created_at >= start_datetime) &
                (Ticket.created_at <= end_datetime) &
                (Ticket.is_deleted == False)
            )
            
        if branch_id:
            query = query.where(Ticket.branch == branch_id)
            
        query = query.group_by(fn.DATE(Ticket.created_at)).order_by(fn.DATE(Ticket.created_at))
        
        results = []
        for row in query:
            # Get parts used for this date
            parts_query = (RepairPart
                .select(fn.SUM(RepairPart.quantity).alias('total_parts'))
                .join(Ticket)
                .where(
                    (fn.DATE(Ticket.created_at) == row.date) &
                    (Ticket.is_deleted == False)
                )
            )
            parts_used = parts_query.scalar() or 0
            
            results.append({
                'date': str(row.date),
                'new_tickets': row.new_tickets,
                'completed': row.completed,
                'in_progress': row.in_progress,
                'total_revenue': float(row.total_revenue or 0),
                'parts_used': int(parts_used)
            })
        
        return results
    
    def get_technician_performance(self, start_date: date, end_date: date, branch_id: Optional[int] = None) -> List[Dict]:
        """Generate technician performance report.
        
        Returns:
            List with tech stats: tickets, completion time, revenue, success rate.
        """
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Query for technician performance
        query = (Ticket
            .select(
                Technician.id.alias('tech_id'),
                Technician.full_name.alias('technician_name'),
                fn.COUNT(Ticket.id).alias('total_tickets'),
                fn.SUM(Case(None, [(Ticket.status == 'completed', 1)], 0)).alias('tickets_completed'),
                fn.SUM(Ticket.estimated_cost).alias('total_revenue')
            )
            .join(Technician, on=(Ticket.assigned_technician == Technician.id))
            .where(
                (Ticket.created_at >= start_datetime) &
                (Ticket.created_at <= end_datetime) &
                (Ticket.is_deleted == False) &
                (Ticket.assigned_technician.is_null(False))
            )
        )
        if branch_id:
            query = query.where(Ticket.branch == branch_id)
            
        query = query.group_by(Technician.id, Technician.full_name) \
            .order_by(fn.SUM(Ticket.estimated_cost).desc()) \
            .dicts()
        
        results = []
        for row in query:
            # Calculate average completion time for completed tickets
            completed_query = (Ticket
                .select(
                    fn.AVG(
                        (fn.JULIANDAY(Ticket.completed_at) - fn.JULIANDAY(Ticket.created_at)) * 24
                    ).alias('avg_hours')
                )
                .where(
                    (Ticket.assigned_technician == row['tech_id']) &
                    (Ticket.status == 'completed') &
                    (Ticket.completed_at.is_null(False)) &
                    (Ticket.created_at >= start_datetime) &
                    (Ticket.created_at <= end_datetime) &
                    (Ticket.is_deleted == False)
                )
            )
            if branch_id:
                completed_query = completed_query.where(Ticket.branch == branch_id)
            
            avg_time = completed_query.scalar() or 0
            success_rate = (row['tickets_completed'] / row['total_tickets'] * 100) if row['total_tickets'] > 0 else 0
            
            # Simple bonus calculation (e.g., 5% of revenue generated)
            bonus = float(row['total_revenue'] or 0) * 0.05
            
            results.append({
                'technician_name': row['technician_name'],
                'total_tickets': row['total_tickets'],
                'tickets_completed': row['tickets_completed'],
                'avg_completion_time': float(avg_time),
                'total_revenue': float(row['total_revenue'] or 0),
                'success_rate': float(success_rate),
                'estimated_bonus': float(bonus)
            })
        
        return results

    def get_work_log_summary(self, start_date: date, end_date: date, branch_id: Optional[int] = None) -> List[Dict]:
        """Generate work log summary report (hours worked, efficiency)."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Query for work log summary (calculate hours from start/end times)
        query = (WorkLog
            .select(
                Technician.id.alias('tech_id'),
                Technician.full_name.alias('technician_name'),
                fn.COUNT(WorkLog.id).alias('sessions'),
                fn.SUM(
                    (fn.JULIANDAY(WorkLog.end_time) - fn.JULIANDAY(WorkLog.start_time)) * 24
                ).alias('total_hours')
            )
            .join(Technician, on=(WorkLog.technician == Technician.id))
            .join(Ticket, on=(WorkLog.ticket == Ticket.id))
            .where(
                (WorkLog.start_time >= start_datetime) &
                (WorkLog.start_time <= end_datetime) &
                (WorkLog.end_time.is_null(False))
            )
        )
        if branch_id:
            query = query.where(Ticket.branch == branch_id)
            
        query = query.group_by(Technician.id, Technician.full_name) \
            .order_by(fn.SUM((fn.JULIANDAY(WorkLog.end_time) - fn.JULIANDAY(WorkLog.start_time)) * 24).desc()) \
            .dicts()
        
        results = []
        for row in query:
            # Get tickets worked on by this technician
            tickets_query = (Ticket
                .select(fn.COUNT(Ticket.id))
                .where(
                    (Ticket.assigned_technician == row['tech_id']) &
                    (Ticket.created_at >= start_datetime) &
                    (Ticket.created_at <= end_datetime) &
                    (Ticket.is_deleted == False)
                )
            )
            if branch_id:
                tickets_query = tickets_query.where(Ticket.branch == branch_id)
            
            tickets_count = tickets_query.scalar() or 0
            
            avg_per_ticket = row['total_hours'] / tickets_count if tickets_count > 0 else 0
            
            # Calculate efficiency (sessions per hour - lower is better)
            efficiency = row['sessions'] / row['total_hours'] if row['total_hours'] > 0 else 0
            
            results.append({
                'technician_name': row['technician_name'],
                'sessions': row['sessions'],
                'total_hours': float(row['total_hours'] or 0),
                'avg_per_ticket': float(avg_per_ticket),
                'billable_hours': float(row['total_hours'] or 0),  # Assuming all hours are billable
                'efficiency': f"{efficiency:.2f}"
            })
        
        return results

    # ==================== FINANCIAL REPORTS ====================

    def get_revenue_summary(self, start_date: date, end_date: date, branch_id: Optional[int] = None) -> Dict:
        """Generate revenue summary report including profit margins."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Total revenue for period
        total_query = Ticket.select(
                fn.SUM(Ticket.estimated_cost).alias('total'),
                fn.COUNT(Ticket.id).alias('count')
            ).where(
                (Ticket.status == 'completed') &
                (Ticket.completed_at >= start_datetime) &
                (Ticket.completed_at <= end_datetime) &
                (Ticket.is_deleted == False)
            )
        if branch_id:
            total_query = total_query.where(Ticket.branch == branch_id)
        
        total_row = total_query.get()
        total_revenue = float(total_row.total or 0)
        ticket_count = total_row.count
        avg_revenue = total_revenue / ticket_count if ticket_count > 0 else 0
        
        # Calculate Parts Cost
        parts_cost_query = (RepairPart
            .select(fn.SUM(RepairPart.quantity * Part.cost_price).alias('total_cost'))
            .join(Part)
            .switch(RepairPart)
            .join(Ticket)
            .where(
                (Ticket.status == 'completed') &
                (Ticket.completed_at >= start_datetime) &
                (Ticket.completed_at <= end_datetime) &
                (Ticket.is_deleted == False)
            )
        )
        if branch_id:
            parts_cost_query = parts_cost_query.where(Ticket.branch == branch_id)
            
        total_parts_cost = float(parts_cost_query.scalar() or 0)
        
        gross_profit = total_revenue - total_parts_cost
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Daily breakdown
        daily_query = Ticket.select(
                fn.DATE(Ticket.completed_at).alias('date'),
                fn.SUM(Ticket.estimated_cost).alias('revenue'),
                fn.COUNT(Ticket.id).alias('count')
            ).where(
                (Ticket.status == 'completed') &
                (Ticket.completed_at >= start_datetime) &
                (Ticket.completed_at <= end_datetime) &
                (Ticket.is_deleted == False)
            )
        if branch_id:
            daily_query = daily_query.where(Ticket.branch == branch_id)
            
        daily_query = daily_query.group_by(fn.DATE(Ticket.completed_at)).order_by(fn.DATE(Ticket.completed_at))
        
        daily_breakdown = []
        for row in daily_query:
            daily_breakdown.append({
                'date': str(row.date),
                'revenue': float(row.revenue or 0),
                'count': row.count
            })
        
        # Previous period comparison
        period_days = (end_date - start_date).days + 1
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date - timedelta(days=1)
        prev_start_dt = datetime.combine(prev_start, datetime.min.time())
        prev_end_dt = datetime.combine(prev_end, datetime.max.time())
        
        prev_query = Ticket.select(fn.SUM(Ticket.estimated_cost).alias('total')).where(
                (Ticket.status == 'completed') &
                (Ticket.completed_at >= prev_start_dt) &
                (Ticket.completed_at <= prev_end_dt) &
                (Ticket.is_deleted == False)
            )
        if branch_id:
            prev_query = prev_query.where(Ticket.branch == branch_id)
        
        prev_revenue = float(prev_query.scalar() or 0)
        growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        
        return {
            'total_revenue': total_revenue,
            'total_cost': total_parts_cost,
            'gross_profit': gross_profit,
            'profit_margin': profit_margin,
            'ticket_count': ticket_count,
            'avg_revenue_per_ticket': avg_revenue,
            'daily_breakdown': daily_breakdown,
            'previous_period_revenue': prev_revenue,
            'growth_percentage': growth
        }
    
    def get_invoice_report(self, start_date: date, end_date: date, status: Optional[str] = None, branch_id: Optional[int] = None) -> List[Dict]:
        """Generate invoice report (overdue tracking)."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        query = Invoice.select(
                Invoice.invoice_number,
                Invoice.total,
                Invoice.payment_status,
                Invoice.due_date,
                Invoice.created_at
            ).where(
                (Invoice.created_at >= start_datetime) &
                (Invoice.created_at <= end_datetime)
            )
        
        if branch_id:
            query = query.where(Invoice.branch == branch_id)
            
        query = query.order_by(Invoice.created_at.desc())
        
        if status:
            query = query.where(Invoice.payment_status == status)
        
        results = []
        today = date.today()
        
        for invoice in query:
            # Calculate days overdue
            days_overdue = 0
            if invoice.due_date and invoice.payment_status != 'paid':
                # Convert datetime to date for comparison
                due_date_only = invoice.due_date.date() if hasattr(invoice.due_date, 'date') else invoice.due_date
                days_overdue = max(0, (today - due_date_only).days)
            
            results.append({
                'invoice_number': invoice.invoice_number,
                'customer_name': 'N/A',  # Customer not linked in current schema
                'total_amount': float(invoice.total),
                'status': invoice.payment_status,
                'due_date': str(invoice.due_date.date()) if invoice.due_date and hasattr(invoice.due_date, 'date') else (str(invoice.due_date) if invoice.due_date else 'N/A'),
                'days_overdue': days_overdue,
                'payment_method': 'N/A'  # Not available in current schema
            })
        
        return results

    def get_outstanding_payments(self, as_of_date: Optional[date] = None, branch_id: Optional[int] = None) -> List[Dict]:
        """Generate outstanding payments report (aging analysis)."""
        if as_of_date is None:
            as_of_date = date.today()
        
        # Query for unpaid invoices
        query = (Invoice
            .select()
            .where(
                (Invoice.payment_status != 'paid') &
                (Invoice.payment_status != 'cancelled')
            )
        )
        if branch_id:
            query = query.where(Invoice.branch == branch_id)
            
        query = query.order_by(Invoice.due_date)
        
        results = []
        for invoice in query:
            # Calculate days overdue
            days_overdue = 0
            aging_bucket = 'Current'
            
            if invoice.due_date:
                due_date_only = invoice.due_date.date() if hasattr(invoice.due_date, 'date') else invoice.due_date
                days_overdue = max(0, (as_of_date - due_date_only).days)
                
                # Determine aging bucket
                if days_overdue == 0:
                    aging_bucket = 'Current'
                elif days_overdue <= 30:
                    aging_bucket = '1-30 days'
                elif days_overdue <= 60:
                    aging_bucket = '31-60 days'
                elif days_overdue <= 90:
                    aging_bucket = '61-90 days'
                else:
                    aging_bucket = '90+ days'
            
            results.append({
                'invoice_number': invoice.invoice_number,
                'customer_name': 'N/A',  # Customer not linked in current schema
                'amount_due': float(invoice.total),
                'due_date': str(invoice.due_date.date()) if invoice.due_date and hasattr(invoice.due_date, 'date') else (str(invoice.due_date) if invoice.due_date else 'N/A'),
                'days_overdue': days_overdue,
                'aging_bucket': aging_bucket
            })
        
        # Sort by days overdue (most overdue first)
        results.sort(key=lambda x: x['days_overdue'], reverse=True)
        
        return results

    # ==================== INVENTORY & SUPPLY CHAIN REPORTS ====================

    def get_stock_level_report(self, low_stock_only: bool = False, branch_id: Optional[int] = None) -> List[Dict]:
        """Generate stock level report with value valuation."""
        query = Part.select().where(Part.is_active == True)
        
        if branch_id:
            query = query.where(Part.branch == branch_id)
        
        if low_stock_only:
            query = query.where(Part.current_stock <= Part.min_stock_level)
        
        results = []
        for part in query:
            # Determine stock status
            if part.current_stock == 0:
                status = 'Out of Stock'
            elif part.current_stock <= part.min_stock_level:
                status = 'Low Stock'
            else:
                status = 'OK'
            
            total_value = part.current_stock * part.cost_price
            
            results.append({
                'sku': part.sku,
                'name': part.name,
                'quantity': part.current_stock,
                'min_stock_level': part.min_stock_level,
                'status': status,
                'unit_cost': float(part.cost_price),
                'total_value': float(total_value)
            })
        
        # Sort by status priority (Out of Stock, Low Stock, OK)
        status_priority = {'Out of Stock': 0, 'Low Stock': 1, 'OK': 2}
        results.sort(key=lambda x: (status_priority[x['status']], x['name']))
        
        return results

    def get_inventory_movement(self, start_date: date, end_date: date, branch_id: Optional[int] = None) -> List[Dict]:
        """Generate inventory movement report (stock in vs stock out)."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Get parts used (stock out)
        parts_used_query = (RepairPart
            .select(
                Part.id.alias('part_id'),
                Part.sku,
                Part.name,
                fn.SUM(RepairPart.quantity).alias('quantity_used')
            )
            .join(Part, on=(RepairPart.part == Part.id))
            .join(Ticket, on=(RepairPart.ticket == Ticket.id))
            .where(
                (RepairPart.installed_at >= start_datetime) &
                (RepairPart.installed_at <= end_datetime)
            )
        )
        if branch_id:
            parts_used_query = parts_used_query.where(Ticket.branch == branch_id)
            
        parts_used_query = parts_used_query.group_by(Part.id, Part.sku, Part.name).dicts()
        
        # Create a dictionary of parts used
        parts_dict = {}
        for row in parts_used_query:
            parts_dict[row['part_id']] = {
                'sku': row['sku'],
                'name': row['name'],
                'stock_out': row['quantity_used'],
                'stock_in': 0
            }
        
        # Get parts received (stock in) from purchase orders
        parts_received_query = (PurchaseOrderItem
            .select(
                Part.id.alias('part_id'),
                Part.sku,
                Part.name,
                fn.SUM(PurchaseOrderItem.quantity).alias('quantity_received')
            )
            .join(Part, on=(PurchaseOrderItem.part == Part.id))
            .join(PurchaseOrder, on=(PurchaseOrderItem.purchase_order == PurchaseOrder.id))
            .where(
                (PurchaseOrder.order_date >= start_datetime) &
                (PurchaseOrder.order_date <= end_datetime) &
                (PurchaseOrder.status == 'received')
            )
        )
        if branch_id:
            parts_received_query = parts_received_query.where(PurchaseOrder.branch == branch_id)
            
        parts_received_query = parts_received_query.group_by(Part.id, Part.sku, Part.name).dicts()
        
        # Add received quantities
        for row in parts_received_query:
            if row['part_id'] in parts_dict:
                parts_dict[row['part_id']]['stock_in'] = row['quantity_received']
            else:
                parts_dict[row['part_id']] = {
                    'sku': row['sku'],
                    'name': row['name'],
                    'stock_out': 0,
                    'stock_in': row['quantity_received']
                }
        
        # Build results with current stock
        results = []
        for part_id, data in parts_dict.items():
            # Get current stock
            part = Part.get_by_id(part_id)
            net_change = data['stock_in'] - data['stock_out']
            movement_value = net_change * part.cost_price
            
            results.append({
                'part_name': data['name'],
                'stock_in': data['stock_in'],
                'stock_out': data['stock_out'],
                'current_stock': part.current_stock,
                'net_change': net_change,
                'movement_value': float(movement_value)
            })
        
        # Sort by absolute net change (most movement first)
        results.sort(key=lambda x: abs(x['net_change']), reverse=True)
        
        return results

    def get_supplier_performance(self, start_date: date, end_date: date, branch_id: Optional[int] = None) -> List[Dict]:
        """Generate supplier performance report (delivery times, on-time rate)."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Query for supplier performance
        query = (PurchaseOrder
            .select(
                Supplier.id.alias('supplier_id'),
                Supplier.name.alias('supplier_name'),
                fn.COUNT(PurchaseOrder.id).alias('total_orders'),
                fn.SUM(PurchaseOrder.total_amount).alias('total_value')
            )
            .join(Supplier, on=(PurchaseOrder.supplier == Supplier.id))
            .where(
                (PurchaseOrder.order_date >= start_datetime) &
                (PurchaseOrder.order_date <= end_datetime)
            )
        )
        if branch_id:
            query = query.where(PurchaseOrder.branch == branch_id)
            
        query = query.group_by(Supplier.id, Supplier.name) \
            .order_by(fn.SUM(PurchaseOrder.total_amount).desc()) \
            .dicts()
        
        results = []
        for row in query:
            # Calculate average delivery time for completed orders
            completed_orders_query = (PurchaseOrder
                .select(
                    fn.AVG(
                        (fn.JULIANDAY(PurchaseOrder.received_date) - fn.JULIANDAY(PurchaseOrder.order_date))
                    ).alias('avg_days')
                )
                .where(
                    (PurchaseOrder.supplier == row['supplier_id']) &
                    (PurchaseOrder.status == 'received') &
                    (PurchaseOrder.received_date.is_null(False)) &
                    (PurchaseOrder.order_date >= start_datetime) &
                    (PurchaseOrder.order_date <= end_datetime)
                )
            )
            if branch_id:
                completed_orders_query = completed_orders_query.where(PurchaseOrder.branch == branch_id)
            
            avg_delivery = completed_orders_query.scalar() or 0
            
            # Calculate on-time delivery rate (assuming 7 days is expected)
            on_time_query = (PurchaseOrder
                .select(fn.COUNT(PurchaseOrder.id))
                .where(
                    (PurchaseOrder.supplier == row['supplier_id']) &
                    (PurchaseOrder.status == 'received') &
                    (PurchaseOrder.received_date.is_null(False)) &
                    (fn.JULIANDAY(PurchaseOrder.received_date) - fn.JULIANDAY(PurchaseOrder.order_date) <= 7) &
                    (PurchaseOrder.order_date >= start_datetime) &
                    (PurchaseOrder.order_date <= end_datetime)
                )
            )
            if branch_id:
                on_time_query = on_time_query.where(PurchaseOrder.branch == branch_id)
            
            on_time_count = on_time_query.scalar() or 0
            
            total_received_query = (PurchaseOrder
                .select(fn.COUNT(PurchaseOrder.id))
                .where(
                    (PurchaseOrder.supplier == row['supplier_id']) &
                    (PurchaseOrder.status == 'received') &
                    (PurchaseOrder.order_date >= start_datetime) &
                    (PurchaseOrder.order_date <= end_datetime)
                )
            )
            if branch_id:
                total_received_query = total_received_query.where(PurchaseOrder.branch == branch_id)
            
            total_received = total_received_query.scalar() or 0
            
            on_time_rate = (on_time_count / total_received * 100) if total_received > 0 else 0
            
            results.append({
                'supplier_name': row['supplier_name'],
                'total_orders': row['total_orders'],
                'total_value': float(row['total_value'] or 0),
                'avg_delivery_days': float(avg_delivery),
                'on_time_rate': float(on_time_rate),
                'quality_issues': 0
            })
        
        return results

    # ==================== CRM REPORTS ====================

    def get_customer_activity(self, start_date: date, end_date: date, branch_id: Optional[int] = None) -> List[Dict]:
        """Generate customer activity report (spend, visit frequency)."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Query for customer activity (join through Device)
        query = (Ticket
            .select(
                Customer.id.alias('customer_id'),
                Customer.name.alias('customer_name'),
                fn.COUNT(Ticket.id).alias('total_tickets'),
                fn.SUM(Ticket.estimated_cost).alias('total_spent'),
                fn.MAX(Ticket.created_at).alias('last_visit')
            )
            .join(Device, on=(Ticket.device == Device.id))
            .join(Customer, on=(Device.customer == Customer.id))
            .where(
                (Ticket.created_at >= start_datetime) &
                (Ticket.created_at <= end_datetime) &
                (Ticket.is_deleted == False)
            )
        )
        if branch_id:
            query = query.where(Ticket.branch == branch_id)
            
        query = query.group_by(Customer.id, Customer.name) \
            .order_by(fn.SUM(Ticket.estimated_cost).desc()) \
            .dicts()
        
        results = []
        today = date.today()
        
        for row in query:
            # Determine customer status
            last_visit_date = row['last_visit'].date() if hasattr(row['last_visit'], 'date') else row['last_visit']
            days_since_visit = (today - last_visit_date).days if last_visit_date else 999
            
            if days_since_visit <= 30:
                status = 'Active'
            elif days_since_visit <= 90:
                status = 'Recent'
            else:
                status = 'Inactive'
            
            avg_value = row['total_spent'] / row['total_tickets'] if row['total_tickets'] > 0 else 0
            
            results.append({
                'customer_name': row['customer_name'],
                'total_tickets': row['total_tickets'],
                'total_spent': float(row['total_spent'] or 0),
                'last_visit': str(last_visit_date) if last_visit_date else 'N/A',
                'status': status,
                'avg_value': float(avg_value)
            })
        
        return results
