"""TicketService - Core Repair Ticket Management.

This service manages the lifecycle of repair tickets, including creation,
status transitions, technician assignment, and integration with:
- Audit Logs
- Status History
- Work Logs (automated time tracking)
- Device Status synchronization
- Dashboard Statistics
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from interfaces.iticket_service import ITicketService
from repositories.ticket_repository import TicketRepository
from repositories.status_history_repository import StatusHistoryRepository
from services.audit_service import AuditService
from dtos.ticket_dto import TicketDTO
from models.user import User
from models.ticket import Ticket


class TicketService(ITicketService):
    """Service class for Ticket operations."""
    
    def __init__(self, audit_service: Optional[AuditService] = None, repository: Optional[TicketRepository] = None):
        """Initialize TicketService.
        
        Args:
            audit_service: Service for logging security/audit events
            repository: Ticket repository (injected or default)
        """
        self.repository = repository or TicketRepository()
        self.audit_service = audit_service or AuditService()
        self.status_history_repository = StatusHistoryRepository()
        
        # Import work log repository for automatic time tracking
        # Imported here to avoid circular imports if WorkLogRepository imports Ticket models
        from repositories.work_log_repository import WorkLogRepository
        self.work_log_repository = WorkLogRepository()
        
    def create_ticket(self, ticket_data: dict, current_user: Optional[User] = None, ip_address: Optional[str] = None) -> TicketDTO:
        """Create a new ticket.
        
        - Auto-assigns to Main Branch (ID=1) if not specified.
        - Automatically starts a work log if a technician is assigned.
        
        Returns:
            TicketDTO: The created ticket (excluding ticket number which is auto-generated in model/repo)
        """
        # Ensure 'ticket_number' is not manually set here as repo handles generation
        ticket_data.pop('ticket_number', None)
        
        # Auto-assign to Main Branch (ID=1) if not specified
        if 'branch' not in ticket_data or ticket_data['branch'] is None:
            ticket_data['branch'] = 1
        
        ticket_model = self.repository.create(ticket_data)
        ticket_dto = TicketDTO.from_model(ticket_model)
        
        self.audit_service.log_action(
            user=current_user,
            action="ticket_create",
            table_name="tickets",
            new_data=ticket_dto.to_audit_dict(),
            ip_address=ip_address
        )
        
        # If ticket was created with an assigned technician, start work log automatically
        if ticket_model.assigned_technician:
            self._start_work_log_for_assignment(ticket_model.id, ticket_model.assigned_technician.id)
        
        return ticket_dto
        
    def get_ticket(self, ticket_id: int, include_deleted: bool = False) -> Optional[TicketDTO]:
        """Get a ticket by ID."""
        ticket_model = self.repository.get(ticket_id, include_deleted)
        return TicketDTO.from_model(ticket_model) if ticket_model else None
        
    def update_ticket(self, ticket_id: int, update_data: dict, current_user: Optional[User] = None, ip_address: Optional[str] = None) -> Optional[TicketDTO]:
        """Update an existing ticket."""
        old_ticket_model = self.repository.get(ticket_id, include_deleted=True)
        if not old_ticket_model:
            return None
            
        old_ticket_dto = TicketDTO.from_model(old_ticket_model)
        
        # Automatically set completed_at when status changes to 'completed'
        if 'status' in update_data and update_data['status'] == 'completed':
            if 'completed_at' not in update_data:
                update_data['completed_at'] = datetime.now()
        
        if 'assigned_technician' in update_data:
            new_tech_id = update_data['assigned_technician']
            old_tech = old_ticket_model.assigned_technician
            old_tech_id = old_tech.id if old_tech else None
            
            if old_tech_id != new_tech_id:
                # Close old work logs
                if old_tech_id:
                     try:
                        active_logs = self.work_log_repository.get_for_ticket(ticket_id)
                        for log in active_logs:
                            if log.technician.id == old_tech_id and not log.end_time:
                                self.work_log_repository.update(log.id, {
                                    'end_time': datetime.now(),
                                    'work_performed': f"{log.work_performed} | Transferred (Update)"
                                })
                     except Exception as e:
                        print(f"Error closing work log in update: {e}")
                
        ticket_model = self.repository.update(ticket_id, update_data)
        if ticket_model:
            ticket_dto = TicketDTO.from_model(ticket_model)
            
            # Start new work log if technician assigned via update
            if 'assigned_technician' in update_data:
                 new_tech_id = update_data['assigned_technician']
                 # Only start if it wasn't already assigned to this tech (to avoid duplicates if logic re-runs)
                 # Actually _start_work_log_for_assignment checks for duplicates
                 if new_tech_id:
                     self._start_work_log_for_assignment(ticket_id, new_tech_id)
            
            self.audit_service.log_action(
                user=current_user,
                action="ticket_update",
                table_name="tickets",
                old_data=old_ticket_dto.to_audit_dict(),
                new_data=ticket_dto.to_audit_dict(),
                ip_address=ip_address
            )
            return ticket_dto
        return None
        
    def delete_ticket(self, ticket_id: int, current_user: Optional[User] = None, ip_address: Optional[str] = None) -> bool:
        """Soft delete a ticket."""
        ticket_model = self.repository.get(ticket_id, include_deleted=True)
        if not ticket_model:
            return False
            
        ticket_dto = TicketDTO.from_model(ticket_model)
        success = self.repository.delete(ticket_id)
        
        if success:
            self.audit_service.log_action(
                user=current_user,
                action="ticket_delete",
                table_name="tickets",
                old_data=ticket_dto.to_audit_dict(),
                ip_address=ip_address
            )
        return success
        
    def restore_ticket(self, ticket_id: int, current_user: Optional[User] = None, ip_address: Optional[str] = None) -> bool:
        """Restore a soft-deleted ticket."""
        ticket_model = self.repository.get(ticket_id, include_deleted=True)
        if not ticket_model:
            return False
            
        ticket_dto = TicketDTO.from_model(ticket_model)
        success = self.repository.restore(ticket_id)
        
        if success:
            self.audit_service.log_action(
                user=current_user,
                action="ticket_restore",
                table_name="tickets",
                new_data=ticket_dto.to_audit_dict(),
                ip_address=ip_address
            )
        return success
        
    def change_ticket_status(self, ticket_id: int, new_status: str, reason: str = None, current_user: Optional[User] = None, ip_address: Optional[str] = None) -> Optional[TicketDTO]:
        """Change ticket status and trigger related workflows.
        
        Workflows triggered:
        1. Logs status change in audit.
        2. Creates status history entry with reason.
        3. Updates associated Device status.
        4. Ends active work logs if completed/cancelled.
        """
        ticket_model = self.repository.get(ticket_id)
        if ticket_model:
            old_status = ticket_model.status
            
            # Don't update if status is the same
            if old_status == new_status:
                return TicketDTO.from_model(ticket_model)
            
            update_data = {'status': new_status}
            if new_status == 'completed':
                update_data['completed_at'] = datetime.now()
                
            updated_ticket = self.update_ticket(ticket_id, update_data, current_user, ip_address)
            if updated_ticket:
                # Log status change in audit
                self.audit_service.log_action(
                    user=current_user,
                    action="ticket_status_change",
                    table_name="tickets",
                    old_data={'status': old_status},
                    new_data={'status': new_status},
                    ip_address=ip_address
                )
                
                # Extract user ID for Peewee (handles User model, UserDTO, or int)
                changed_by_val = current_user
                if hasattr(current_user, 'id'):
                    changed_by_val = current_user.id

                # Create status history entry
                self.status_history_repository.create_status_history({
                    'ticket': ticket_id,
                    'old_status': old_status,
                    'new_status': new_status,
                    'reason': reason,
                    'changed_by': changed_by_val
                })
                
                # Update device status based on ticket status
                self._update_device_status(ticket_model, new_status)
                
                # Automatically end work log when ticket is completed or cancelled
                if new_status in ['completed', 'cancelled']:
                    self._end_active_work_logs(ticket_id)
                
            return updated_ticket
        return None
        
    def assign_ticket(self, ticket_id: int, technician_id: int, reason: str = None, current_user: Optional[User] = None, ip_address: Optional[str] = None) -> Optional[TicketDTO]:
        """Assign ticket to a technician and auto-start work log."""
        ticket_model = self.repository.get(ticket_id)
        if ticket_model:
            old_technician = ticket_model.assigned_technician
            update_data = {'assigned_technician': technician_id}
            
            # If changing technician, end work log for the old technician
            if old_technician and old_technician.id != technician_id:
                # Find active log for old technician on this ticket
                try:
                    active_logs = self.work_log_repository.get_for_ticket(ticket_id)
                    for log in active_logs:
                        if log.technician.id == old_technician.id and not log.end_time:
                            # Close the log
                            update_params = {'end_time': datetime.now()}
                            if reason:
                                new_desc = f"{log.work_performed} | Transferred: {reason}"
                                update_params['work_performed'] = new_desc[:255] # Ensure it fits
                                
                            self.work_log_repository.update(log.id, update_params)
                except Exception as e:
                    print(f"Error closing old work log: {e}")
            
            updated_ticket = self.update_ticket(ticket_id, update_data, current_user, ip_address)
            if updated_ticket:
                self.audit_service.log_action(
                    user=current_user,
                    action="ticket_assign",
                    table_name="tickets",
                    old_data={'assigned_technician': old_technician.id if old_technician else None},
                    new_data={'assigned_technician': technician_id},
                    ip_address=ip_address
                )
                
                # Automatically start work log when ticket is assigned
                if technician_id:
                    self._start_work_log_for_assignment(ticket_id, technician_id)
                
            return updated_ticket
        return None


        
    def list_tickets(self, filters: dict = None) -> List[TicketDTO]:
        """List tickets with optional dictionary filters."""
        ticket_models = self.repository.list_all(filters)
        return [TicketDTO.from_model(ticket) for ticket in ticket_models]
        
    def search_tickets(self, search_term: str) -> List[TicketDTO]:
        """Search tickets by number, customer, or serial."""
        ticket_models = self.repository.search(search_term)
        return [TicketDTO.from_model(ticket) for ticket in ticket_models]
    
    def get_last_today_ticket(self, date):
        """Get the last ticket created today for numbering purposes.
        
        Args:
            date: string in YYYY-MM-DD format (usually)
        """
        # Using model direct access for specific query
        return Ticket.select().where(
            Ticket.ticket_number.startswith(f"RPT-{date}")
        ).order_by(Ticket.ticket_number.desc()).first()

    def get_dashboard_stats(self, date=None, branch_id: Optional[int] = None) -> dict:
        """Get daily dashboard stats (new, completed, revenue)."""
        return self.repository.get_dashboard_stats(date, branch_id)
        
    def get_recent_tickets(self, limit: int = 10, branch_id: Optional[int] = None) -> List[TicketDTO]:
        """Get a list of recently created tickets."""
        ticket_models = self.repository.get_recent(limit, branch_id)
        return [TicketDTO.from_model(ticket) for ticket in ticket_models]
    
    def get_status_history(self, ticket_id: int, limit: int = 100):
        """Get status change history for a ticket."""
        return self.status_history_repository.get_history_for_ticket(ticket_id, limit)
        
    def get_tickets_by_technician(self, technician_id: int, limit: int = 50) -> List[TicketDTO]:
        """Get tickets assigned to a specific technician."""
        # Use repository's list functionality with filter
        filters = {'technician_id': technician_id}
        tickets = self.repository.list_all(filters)
        # Sort manually if repository relies on default ordering (usually created_at desc)
        # Assuming list_all handles filtering
        if limit:
            tickets = tickets[:limit]
        return [TicketDTO.from_model(t) for t in tickets]
    
    # Enhanced dashboard methods
    def get_dashboard_stats_range(self, start_date, end_date, branch_id: Optional[int] = None) -> dict:
        """Get dashboard statistics for a date range."""
        return self.repository.get_dashboard_stats_range(start_date, end_date, branch_id)
    
    def get_technician_performance(self, start_date, end_date, branch_id: Optional[int] = None) -> List[dict]:
        """Get technician performance statistics."""
        return self.repository.get_technician_performance(start_date, end_date, branch_id)
    
    def get_status_distribution(self, start_date, end_date, branch_id: Optional[int] = None) -> dict:
        """Get ticket status distribution."""
        return self.repository.get_status_distribution(start_date, end_date)
    
    def get_revenue_trend(self, start_date, end_date, branch_id: Optional[int] = None) -> List[dict]:
        """Get revenue trend over time."""
        return self.repository.get_revenue_trend(start_date, end_date, branch_id)
    
    def get_average_completion_time(self, start_date, end_date, branch_id: Optional[int] = None) -> float:
        """Get average completion time in hours."""
        return self.repository.get_average_completion_time(start_date, end_date, branch_id)
    
    def _update_device_status(self, ticket_model, new_ticket_status: str):
        """Update device status based on ticket status.
        
        Maps ticket workflow stages to device physical status.
        """
        if not ticket_model.device:
            return
        
        # Map ticket status to device status
        # Device statuses: 'received', 'diagnosed', 'repairing', 'repaired', 'completed', 'returned'
        status_mapping = {
            'open': 'received',           # Ticket opened → Device received
            'diagnosed': 'diagnosed',     # Ticket diagnosed → Device diagnosed
            'in_progress': 'repairing',   # Ticket in progress → Device being repaired
            'awaiting_parts': 'repairing', # Waiting for parts → Still repairing
            'completed': 'repaired',      # Ticket completed → Device repaired (ready for pickup)
            'cancelled': 'received',      # Ticket cancelled → Reset to received
            'unrepairable': 'completed'   # Unrepairable → Mark as completed/returned
        }
        
        new_device_status = status_mapping.get(new_ticket_status)
        if new_device_status and ticket_model.device.status != new_device_status:
            # Update device status
            from models.device import Device
            device = Device.get_by_id(ticket_model.device.id)
            if device:
                device.status = new_device_status
                device.save()
    
    def _start_work_log_for_assignment(self, ticket_id: int, technician_id: int):
        """Automatically start a work log when a ticket is assigned to a technician."""
        try:
            # Check if there's already an active work log for this ticket and technician
            active_logs = self.work_log_repository.get_active_for_technician(technician_id)
            ticket_has_active_log = any(log.ticket_id == ticket_id for log in active_logs)
            
            if not ticket_has_active_log:
                # Create a new work log
                self.work_log_repository.create({
                    'technician': technician_id,
                    'ticket': ticket_id,
                    'work_performed': 'Ticket assigned - work started',
                    'start_time': datetime.now()
                })
        except Exception as e:
            # Log error but don't fail the assignment
            print(f"Error creating work log: {e}")
    
    def _end_active_work_logs(self, ticket_id: int):
        """Automatically end all active work logs for a ticket when it's completed or cancelled."""
        try:
            # Get all work logs for this ticket
            work_logs = self.work_log_repository.get_for_ticket(ticket_id)
            
            # End any active logs (where end_time is null)
            for log in work_logs:
                if not log.end_time:
                    self.work_log_repository.update(log.id, {
                        'end_time': datetime.now()
                    })
        except Exception as e:
            # Log error but don't fail the status change
            print(f"Error ending work logs: {e}")