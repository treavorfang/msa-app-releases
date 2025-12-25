"""
Device Model - Device Tracking and Management.

Manages devices brought in for repair including identification, condition tracking,
and status management throughout the repair lifecycle.

Features:
    - Comprehensive device identification (brand, model, serial, IMEI)
    - Automatic barcode generation (DEV-BranchIDYYMMDD-XXXX format)
    - Device condition and lock type tracking
    - Status workflow (received → diagnosed → repairing → repaired → completed → returned)
    - Customer ownership tracking
    - Branch association
    - Soft delete support

Example:
    >>> # Create device
    >>> device = Device.create(
    ...     brand="Apple",
    ...     model="iPhone 13 Pro",
    ...     serial_number="ABC123456",
    ...     imei="123456789012345",
    ...     color="Graphite",
    ...     condition="Screen cracked, back intact",
    ...     customer=customer,
    ...     branch=branch
    ... )
    >>> print(device.barcode)  # Auto-generated: DEV-1241207-0001
    
    >>> # Update status
    >>> device.status = 'repairing'
    >>> device.save()
    
    >>> # Get device tickets
    >>> tickets = device.tickets

Database Schema:
    Table: devices
    Columns:
        - id: Primary key
        - brand: Device brand (max 50 chars)
        - model: Device model (max 50 chars)
        - serial_number: Serial number (max 100 chars)
        - imei: IMEI number (15 chars, unique)
        - color: Device color (max 20 chars)
        - passcode: Device passcode/PIN (max 50 chars)
        - condition: Physical condition description
        - lock_type: Lock type (e.g., "Face ID", "Passcode")
        - status: Current status (choices)
        - barcode: Auto-generated barcode (max 50 chars)
        - customer_id: Owner foreign key
        - branch_id: Branch foreign key
        - received_at: When device was received
        - completed_at: When repair was completed
        - is_deleted: Soft delete flag
        - deleted_at: Deletion timestamp

Relationships:
    - customer: Many-to-One (Device -> Customer)
    - branch: Many-to-One (Device -> Branch)
    - tickets: One-to-Many (Device -> Ticket) [backref]

See Also:
    - models.customer.Customer: Device owner
    - models.ticket.Ticket: Repair tickets for device
    - models.branch.Branch: Branch handling device
"""

import re
from datetime import datetime
from peewee import (
    AutoField, CharField, TextField, ForeignKeyField,
    BooleanField, DateTimeField
)
from models.base_model import BaseModel
from models.customer import Customer
from models.branch import Branch


class Device(BaseModel):
    """
    Device model for tracking repair items.
    
    Attributes:
        id (int): Primary key
        brand (str): Device brand
        model (str): Device model
        serial_number (str): Serial number
        imei (str): IMEI number (unique)
        color (str): Device color
        passcode (str): Device passcode/PIN
        condition (str): Physical condition
        lock_type (str): Lock type
        status (str): Current status
        barcode (str): Auto-generated barcode
        customer (Customer): Device owner
        branch (Branch): Associated branch
        received_at (datetime): When received
        completed_at (datetime): When completed
        is_deleted (bool): Soft delete flag
        deleted_at (datetime): Deletion timestamp
    """
    
    id = AutoField(help_text="Primary key")
    
    # ==================== Device Identification ====================
    
    brand = CharField(
        max_length=50,
        help_text="Device brand (e.g., 'Apple', 'Samsung')"
    )
    
    model = CharField(
        max_length=50,
        help_text="Device model (e.g., 'iPhone 13 Pro')"
    )
    
    serial_number = CharField(
        max_length=100,
        null=True,
        help_text="Device serial number"
    )
    
    imei = CharField(
        max_length=15,
        null=True,
        unique=True,
        help_text="IMEI number (unique identifier)"
    )
    
    barcode = CharField(
        max_length=50,
        null=True,
        help_text="Auto-generated barcode (DEV-BranchIDYYMMDD-XXXX)"
    )
    
    # ==================== Device Details ====================
    
    color = CharField(
        max_length=20,
        null=True,
        help_text="Device color"
    )
    
    passcode = CharField(
        max_length=50,
        null=True,
        help_text="Device passcode/PIN for testing"
    )
    
    condition = TextField(
        null=True,
        help_text="Physical condition description"
    )
    
    lock_type = CharField(
        max_length=50,
        null=True,
        help_text="Lock type (e.g., 'Face ID', 'Passcode', 'Pattern')"
    )
    
    # ==================== Status ====================
    
    status = CharField(
        choices=['received', 'diagnosed', 'repairing', 'repaired', 'completed', 'returned'],
        default='received',
        max_length=20,
        help_text="Current device status"
    )
    
    # ==================== Relationships ====================
    
    customer = ForeignKeyField(
        Customer,
        backref='devices',
        on_delete='CASCADE',
        help_text="Device owner"
    )
    
    branch = ForeignKeyField(
        Branch,
        backref='devices',
        on_delete='SET NULL',
        null=True,
        help_text="Branch handling this device"
    )
    
    # ==================== Timestamps ====================
    
    received_at = DateTimeField(
        default=datetime.now,
        help_text="When device was received"
    )
    
    completed_at = DateTimeField(
        null=True,
        help_text="When repair was completed"
    )
    
    updated_at = DateTimeField(
        default=datetime.now,
        help_text="When device was last updated"
    )

    # ==================== Soft Delete ====================
    
    is_deleted = BooleanField(
        default=False,
        help_text="Soft delete flag"
    )
    
    deleted_at = DateTimeField(
        null=True,
        help_text="When device was deleted"
    )
    
    class Meta:
        """Model metadata."""
        table_name = 'devices'
        indexes = (
            (('imei',), True),  # Unique index
            (('serial_number',), False),
            (('barcode',), False),
            (('status',), False),
        )
    
    # ==================== Class Methods ====================
    
    @classmethod
    def generate_barcode(cls, branch_id=None):
        """
        Generate unique barcode in DEV-BranchIDYYMMDD-XXXX format.
        
        Format breakdown:
        - DEV: Prefix for "Device"
        - BranchID: Branch identifier (default: 1)
        - YYMMDD: Date in YYMMDD format
        - XXXX: 4-digit sequence number (resets at 9999)
        
        Args:
            branch_id: Branch ID or Branch object (default: 1)
        
        Returns:
            str: Generated barcode (e.g., "DEV-1241207-0001")
        """
        today = datetime.now().strftime("%y%m%d")
        
        if branch_id is None:
            branch_id = 1
        elif hasattr(branch_id, 'id'):
            branch_id = branch_id.id
        
        last_device = cls.select().order_by(cls.barcode.desc()).first()
        
        sequence = 1
        if last_device and last_device.barcode:
            match = re.search(r"-(\d{4})$", last_device.barcode)
            if match:
                sequence = int(match.group(1)) + 1
                if sequence > 9999:
                    sequence = 1
        
        return f"DEV-{branch_id}{today}-{sequence:04d}"
    
    # ==================== Instance Methods ====================
    
    def save(self, *args, **kwargs):
        """
        Save device with automatic barcode generation.
        
        Generates unique barcode if not set. Ensures uniqueness
        by checking existing barcodes.
        
        Raises:
            ValueError: If unique barcode cannot be generated
        """
        if not self.barcode:
            attempts = 0
            while attempts < 5:
                new_barcode = self.generate_barcode(self.branch)
                if not self.__class__.select().where(
                    self.__class__.barcode == new_barcode
                ).exists():
                    self.barcode = new_barcode
                    break
                attempts += 1
            else:
                raise ValueError("Could not generate unique barcode")
        
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
    def __str__(self):
        """String representation."""
        return f"{self.brand} {self.model}"
    
    def __repr__(self):
        """Developer-friendly representation."""
        return f'<Device id={self.id} barcode="{self.barcode}" brand="{self.brand}" model="{self.model}">'
    
    # ==================== Helper Methods ====================
    
    def get_active_tickets(self):
        """Get all active tickets for this device."""
        return list(self.tickets.where(
            self.tickets.model_class.is_deleted == False
        ))
    
    def mark_completed(self):
        """Mark device as completed and set completion timestamp."""
        self.status = 'completed'
        self.completed_at = datetime.now()
        self.save()
    
    def is_in_repair(self):
        """Check if device is currently being repaired."""
        return self.status in ['diagnosed', 'repairing', 'repaired']