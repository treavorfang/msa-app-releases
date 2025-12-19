"""
Customer Model - Customer Management System.

Manages customer information including contact details, preferences, and history.
Customers own devices and are associated with repair tickets.

Features:
    - Contact information (name, phone, email, address)
    - Preferred contact method
    - Branch association
    - Soft delete support
    - Audit trail (created_by, updated_by)
    - Notes for additional information

Example:
    >>> # Create customer
    >>> customer = Customer.create(
    ...     name="John Doe",
    ...     phone="+1234567890",
    ...     email="john@example.com",
    ...     preferred_contact_method="email",
    ...     branch=main_branch,
    ...     created_by=current_user
    ... )
    
    >>> # Get customer's devices
    >>> devices = customer.devices
    
    >>> # Get customer's tickets
    >>> tickets = [d.tickets for d in customer.devices]

Database Schema:
    Table: customers
    Columns:
        - id: Primary key
        - name: Customer name (max 100 chars)
        - phone: Phone number (max 20 chars)
        - email: Email address (max 100 chars)
        - address: Physical address (max 255 chars)
        - preferred_contact_method: Preferred contact (email/phone/sms)
        - notes: Additional notes
        - branch_id: Associated branch
        - created_by_id: User who created record
        - updated_by_id: User who last updated
        - created_at: Creation timestamp
        - updated_at: Last update timestamp
        - is_deleted: Soft delete flag
        - deleted_at: Deletion timestamp

Relationships:
    - branch: Many-to-One (Customer -> Branch)
    - created_by: Many-to-One (Customer -> User)
    - updated_by: Many-to-One (Customer -> User)
    - devices: One-to-Many (Customer -> Device) [backref]

See Also:
    - models.device.Device: Devices owned by customer
    - models.ticket.Ticket: Repair tickets for customer's devices
"""

from datetime import datetime
from peewee import (
    AutoField, CharField, TextField, ForeignKeyField,
    BooleanField, DateTimeField
)
from models.base_model import BaseModel
from models.user import User
from models.branch import Branch


class Customer(BaseModel):
    """
    Customer model for managing customer information.
    
    Attributes:
        id (int): Primary key
        name (str): Customer name
        phone (str): Phone number
        email (str): Email address
        address (str): Physical address
        preferred_contact_method (str): Preferred contact method
        notes (str): Additional notes
        branch (Branch): Associated branch
        created_by (User): User who created record
        updated_by (User): User who last updated
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last update timestamp
        is_deleted (bool): Soft delete flag
        deleted_at (datetime): Deletion timestamp
    """
    
    id = AutoField(help_text="Primary key")
    
    # ==================== Contact Information ====================
    
    name = CharField(
        max_length=100,
        help_text="Customer full name"
    )
    
    phone = CharField(
        max_length=20,
        null=True,
        help_text="Phone number"
    )
    
    email = CharField(
        max_length=100,
        null=True,
        help_text="Email address"
    )
    
    address = CharField(
        max_length=255,
        null=True,
        help_text="Physical address"
    )
    
    preferred_contact_method = CharField(
        choices=['email', 'phone', 'sms'],
        default='phone',
        max_length=10,
        help_text="Preferred contact method"
    )
    
    notes = TextField(
        null=True,
        help_text="Additional notes about customer"
    )
    
    # ==================== Relationships ====================
    
    branch = ForeignKeyField(
        Branch,
        backref='customers',
        on_delete='SET NULL',
        null=True,
        help_text="Associated branch"
    )
    
    created_by = ForeignKeyField(
        User,
        backref='customers_created',
        on_delete='SET NULL',
        null=True,
        help_text="User who created this customer"
    )
    
    updated_by = ForeignKeyField(
        User,
        backref='customers_updated',
        on_delete='SET NULL',
        null=True,
        help_text="User who last updated this customer"
    )
    
    # ==================== Timestamps ====================
    
    created_at = DateTimeField(
        default=datetime.now,
        help_text="When customer was created"
    )
    
    updated_at = DateTimeField(
        default=datetime.now,
        help_text="When customer was last updated"
    )
    
    # ==================== Soft Delete ====================
    
    is_deleted = BooleanField(
        default=False,
        help_text="Soft delete flag"
    )
    
    deleted_at = DateTimeField(
        null=True,
        help_text="When customer was deleted"
    )
    
    class Meta:
        """Model metadata."""
        table_name = 'customers'
        indexes = (
            (('email',), False),
            (('phone',), False),
            (('is_deleted',), False),
        )
    
    def save(self, *args, **kwargs):
        """Save with automatic timestamp update."""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
    def __str__(self):
        """String representation."""
        return self.name
    
    def __repr__(self):
        """Developer-friendly representation."""
        return f'<Customer id={self.id} name="{self.name}">'
    
    def get_devices(self):
        """Get all devices owned by this customer."""
        return list(self.devices.where(self.devices.model_class.is_deleted == False))
    
    def get_active_tickets(self):
        """Get all active tickets for customer's devices."""
        from models.ticket import Ticket
        from models.device import Device
        
        return list(
            Ticket.select()
            .join(Device)
            .where(
                (Device.customer == self) &
                (Ticket.is_deleted == False)
            )
        )