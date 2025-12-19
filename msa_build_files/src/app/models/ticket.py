"""
Ticket Model - Repair Request Management System.

This module defines the Ticket model which represents repair requests in the system.
Tickets link devices to customers, track repair status, manage technician assignments,
and handle financial aspects of repairs.

Features:
    - Automatic ticket number generation (RPT-BranchIDYYMMDD-XXXX format)
    - Status workflow management (Open → In Progress → Completed → Closed)
    - Priority levels (Low, Medium, High, Urgent)
    - Technician assignment and tracking
    - Financial tracking (estimated cost, actual cost, deposits)
    - Warranty coverage tracking
    - Soft delete support
    - Branch-specific ticket management
    - Deadline and completion tracking

Status Workflow:
    OPEN → IN_PROGRESS → COMPLETED → CLOSED
           ↓
    PENDING_PARTS → IN_PROGRESS
           ↓
    CANCELLED (terminal state)

Example:
    >>> # Create a new ticket
    >>> ticket = Ticket.create(
    ...     device=device,
    ...     created_by=user,
    ...     branch=branch,
    ...     error="Screen not working",
    ...     error_description="Display shows black screen",
    ...     estimated_cost=5000.00,
    ...     priority=TicketPriority.HIGH
    ... )
    >>> print(ticket.ticket_number)  # Auto-generated: RPT-1241207-0001
    
    >>> # Assign technician
    >>> ticket.assigned_technician = technician
    >>> ticket.status = TicketStatus.IN_PROGRESS
    >>> ticket.save()
    
    >>> # Complete ticket
    >>> ticket.status = TicketStatus.COMPLETED
    >>> ticket.completed_at = datetime.now()
    >>> ticket.actual_cost = 4500.00
    >>> ticket.save()

Database Schema:
    Table: tickets
    
    Columns:
        - id: Primary key
        - ticket_number: Unique identifier (RPT-BranchIDYYMMDD-XXXX)
        - device_id: Foreign key to Device
        - created_by_id: Foreign key to User (creator)
        - branch_id: Foreign key to Branch
        - assigned_technician_id: Foreign key to Technician
        - approved_by_id: Foreign key to User (approver)
        - status: Current status (choices from TicketStatus)
        - priority: Priority level (choices from TicketPriority)
        - error: Brief error description (max 255 chars)
        - error_description: Detailed error description
        - accessories: Accessories included with device
        - internal_notes: Internal notes for staff
        - estimated_cost: Estimated repair cost
        - actual_cost: Actual repair cost
        - deposit_paid: Deposit amount paid
        - warranty_covered: Whether repair is under warranty
        - deadline: Expected completion date
        - completed_at: When repair was completed
        - created_at: When ticket was created
        - is_deleted: Soft delete flag
        - deleted_at: When ticket was deleted
    
    Indexes:
        - UNIQUE (ticket_number)
        - INDEX (status)
        - INDEX (created_at)
        - INDEX (branch_id)
        - INDEX (is_deleted)
        - INDEX (assigned_technician_id)

Relationships:
    - device: Many-to-One (Ticket -> Device)
    - created_by: Many-to-One (Ticket -> User)
    - branch: Many-to-One (Ticket -> Branch)
    - assigned_technician: Many-to-One (Ticket -> Technician)
    - approved_by: Many-to-One (Ticket -> User)
    - status_history: One-to-Many (Ticket -> StatusHistory)
    - work_logs: One-to-Many (Ticket -> WorkLog)
    - repair_parts: One-to-Many (Ticket -> RepairPart)
    - invoices: One-to-Many (Ticket -> Invoice)

See Also:
    - models.device.Device: Device being repaired
    - models.customer.Customer: Customer who owns the device
    - models.technician.Technician: Assigned technician
    - models.status_history.StatusHistory: Status change tracking
    - models.work_log.WorkLog: Work performed on ticket
    - config.constants.TicketStatus: Status constants
    - config.constants.TicketPriority: Priority constants
"""

import re
from datetime import datetime
from peewee import (
    AutoField,
    CharField,
    TextField,
    ForeignKeyField,
    DecimalField,
    BooleanField,
    DateTimeField
)

from models.base_model import BaseModel
from models.customer import Customer
from models.device import Device
from models.user import User
from models.branch import Branch
from models.technician import Technician
from config.constants import TicketStatus, TicketPriority


class Ticket(BaseModel):
    """
    Ticket model for managing repair requests.
    
    Represents a repair request with full lifecycle tracking from creation
    to completion, including status workflow, technician assignment, and
    financial management.
    
    Attributes:
        id (int): Primary key
        ticket_number (str): Unique ticket identifier (auto-generated)
        device (Device): Device being repaired
        created_by (User): User who created the ticket
        branch (Branch): Branch handling the repair
        assigned_technician (Technician): Technician assigned to repair
        approved_by (User): User who approved the repair
        status (str): Current ticket status
        priority (str): Ticket priority level
        error (str): Brief error description
        error_description (str): Detailed error description
        accessories (str): Accessories included with device
        internal_notes (str): Internal notes for staff
        estimated_cost (Decimal): Estimated repair cost
        actual_cost (Decimal): Actual repair cost
        deposit_paid (Decimal): Deposit amount paid
        warranty_covered (bool): Whether repair is under warranty
        deadline (datetime): Expected completion date
        completed_at (datetime): When repair was completed
        created_at (datetime): When ticket was created
        is_deleted (bool): Soft delete flag
        deleted_at (datetime): When ticket was deleted
    """
    
    # ==================== Primary Key ====================
    
    id = AutoField()
    
    # ==================== Identification ====================
    
    ticket_number = CharField(
        max_length=20,
        unique=True,
        help_text="Unique ticket identifier (RPT-BranchIDYYMMDD-XXXX)"
    )
    
    # ==================== Relationships ====================
    
    device = ForeignKeyField(
        Device,
        backref='tickets',
        on_delete='CASCADE',
        help_text="Device being repaired"
    )
    
    created_by = ForeignKeyField(
        User,
        backref='tickets_opened',
        on_delete='SET NULL',
        null=True,
        help_text="User who created this ticket"
    )
    
    branch = ForeignKeyField(
        Branch,
        backref='tickets',
        on_delete='SET NULL',
        null=True,
        help_text="Branch handling this repair"
    )
    
    assigned_technician = ForeignKeyField(
        Technician,
        backref='tickets_assigned',
        on_delete='SET NULL',
        null=True,
        help_text="Technician assigned to this repair"
    )
    
    approved_by = ForeignKeyField(
        User,
        backref='tickets_approved',
        on_delete='SET NULL',
        null=True,
        help_text="User who approved this repair"
    )
    
    # ==================== Status & Priority ====================
    
    status = CharField(
        choices=TicketStatus.ALL,
        default=TicketStatus.OPEN,
        max_length=20,
        help_text="Current ticket status"
    )
    
    priority = CharField(
        choices=TicketPriority.ALL,
        default=TicketPriority.MEDIUM,
        max_length=10,
        help_text="Ticket priority level"
    )
    
    # ==================== Problem Description ====================
    
    error = CharField(
        max_length=255,
        null=True,
        help_text="Brief error description (max 255 chars)"
    )
    
    error_description = TextField(
        null=True,
        help_text="Detailed error description"
    )
    
    accessories = TextField(
        null=True,
        help_text="Accessories included with device (e.g., charger, case)"
    )
    
    internal_notes = TextField(
        null=True,
        help_text="Internal notes for staff (not visible to customer)"
    )
    
    # ==================== Financial ====================
    
    estimated_cost = DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Estimated repair cost"
    )
    
    actual_cost = DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Actual repair cost (updated on completion)"
    )
    
    deposit_paid = DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Deposit amount paid by customer"
    )
    
    warranty_covered = BooleanField(
        default=False,
        help_text="Whether this repair is covered under warranty"
    )
    
    # ==================== Timing ====================
    
    created_at = DateTimeField(
        default=datetime.now,
        help_text="When this ticket was created"
    )
    
    deadline = DateTimeField(
        null=True,
        help_text="Expected completion date"
    )
    
    completed_at = DateTimeField(
        null=True,
        help_text="When repair was completed"
    )
    
    # ==================== Soft Delete ====================
    
    is_deleted = BooleanField(
        default=False,
        help_text="Soft delete flag"
    )
    
    deleted_at = DateTimeField(
        null=True,
        help_text="When this ticket was deleted"
    )
    
    # ==================== Meta Configuration ====================
    
    class Meta:
        """Model metadata and database configuration."""
        table_name = 'tickets'
        indexes = (
            (('ticket_number',), True),  # Unique index
            (('status',), False),
            (('created_at',), False),
            (('branch',), False),
            (('is_deleted',), False),
            (('assigned_technician',), False),
        )
    
    # ==================== Class Methods ====================
    
    @classmethod
    def generate_ticket_number(cls, branch_id=None):
        """
        Generate unique ticket number in RPT-BranchIDYYMMDD-XXXX format.
        
        Format breakdown:
        - RPT: Prefix for "Repair Ticket"
        - BranchID: Branch identifier (default: 1)
        - YYMMDD: Date in YYMMDD format
        - XXXX: 4-digit sequence number (resets at 9999)
        
        Args:
            branch_id: Branch ID or Branch object (default: 1)
        
        Returns:
            str: Generated ticket number (e.g., "RPT-1241207-0001")
        
        Example:
            >>> ticket_num = Ticket.generate_ticket_number(branch_id=1)
            >>> print(ticket_num)
            'RPT-1241207-0001'
        """
        today = datetime.now().strftime("%y%m%d")  # YYMMDD format
        
        # Default branch_id to 1 if not provided
        if branch_id is None:
            branch_id = 1
        elif hasattr(branch_id, 'id'):  # Handle if Branch object is passed
            branch_id = branch_id.id
        
        # Get the last ticket number globally
        last_ticket = cls.select().order_by(cls.ticket_number.desc()).first()
        
        sequence = 1
        if last_ticket:
            # Match format: RPT-1241122-0001
            # Extract the last 4 digits as sequence
            match = re.search(r"-(\d{4})$", last_ticket.ticket_number)
            if match:
                sequence = int(match.group(1)) + 1
                if sequence > 9999:
                    sequence = 1
        
        return f"RPT-{branch_id}{today}-{sequence:04d}"
    
    # ==================== Instance Methods ====================
    
    def save(self, *args, **kwargs):
        """
        Save ticket with automatic ticket number generation.
        
        If ticket_number is not set, automatically generates one
        based on branch and current date.
        
        Returns:
            int: Number of rows modified
        """
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number(self.branch)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        """String representation showing ticket number and status."""
        return f"{self.ticket_number} - {self.status}"
    
    def __repr__(self):
        """Developer-friendly representation."""
        return f'<Ticket id={self.id} number="{self.ticket_number}" status="{self.status}">'
    
    # ==================== Helper Methods ====================
    
    def get_balance_due(self):
        """
        Calculate remaining balance due.
        
        Returns:
            Decimal: Balance due (actual_cost - deposit_paid)
        """
        return self.actual_cost - self.deposit_paid
    
    def is_overdue(self):
        """
        Check if ticket is past deadline.
        
        Returns:
            bool: True if past deadline and not completed
        """
        if not self.deadline:
            return False
        if self.completed_at:
            return False
        return datetime.now() > self.deadline
    
    def get_customer(self):
        """
        Get customer associated with this ticket.
        
        Returns:
            Customer: Customer who owns the device
        """
        return self.device.customer
    
    def can_be_deleted(self):
        """
        Check if ticket can be deleted.
        
        Tickets with invoices or in certain statuses cannot be deleted.
        
        Returns:
            bool: True if ticket can be deleted
        """
        # Cannot delete if has invoices
        if hasattr(self, 'invoices') and self.invoices.count() > 0:
            return False
        
        # Cannot delete if in progress or completed
        if self.status in [TicketStatus.IN_PROGRESS, TicketStatus.COMPLETED]:
            return False
        
        return True