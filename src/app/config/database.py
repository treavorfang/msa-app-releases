"""
Database configuration and initialization for MSA Application.

This module sets up the SQLite database connection with optimized pragmas
for performance and data integrity. It also handles model registration
and database initialization.

The database uses Write-Ahead Logging (WAL) mode for better concurrency
and performance, with foreign key constraints enabled for data integrity.
"""

from pathlib import Path
from peewee import SqliteDatabase

from config.flags import get_db_path

# ==================== Database Setup ====================

# Initialize SQLite database proxy (deferred initialization)
db = SqliteDatabase(None)

# Optimized SQLite pragmas
DB_PRAGMAS = {
    # Write-Ahead Logging for better concurrency and performance
    'journal_mode': 'wal',
    
    # Enforce foreign key constraints for data integrity
    'foreign_keys': 1,
    
    # Enforce CHECK constraints
    'ignore_check_constraints': 0,
    
    # 64MB cache for better performance
    'cache_size': -64 * 1000,
    
    # Let OS handle fsync (faster, slightly less safe)
    # Use 2 (FULL) for maximum safety in production
    'synchronous': 1,
}


# ==================== Model Registration ====================

def load_models():
    """
    Import and register all models with the database.
    
    This function imports all model classes to ensure they are registered
    with the database proxy. Models must be imported before any database
    operations can be performed.
    
    The models are organized by functional area:
    - Authentication & Authorization (User, Role, Permission)
    - Customers & Devices
    - Tickets & Repairs
    - Inventory & Parts
    - Financial (Invoices, Payments, Purchase Orders)
    - Business Configuration (Branch, Settings, Categories)
    
    Note:
        This function should be called during application initialization,
        before any database queries are executed.
    """
    # Authentication & Authorization
    from models.role import Role
    from models.permission import Permission
    from models.role_permission import RolePermission
    from models.user import User
    from models.audit_log import AuditLog
    
    # Customer & Device Management
    from models.customer import Customer
    from models.device import Device
    
    from models.ticket import Ticket
    from models.ticket_photo import TicketPhoto
    from models.status_history import StatusHistory
    from models.warranty import Warranty
    from models.work_log import WorkLog
    
    # Technician Management
    from models.technician import Technician
    from models.technician_performance import TechnicianPerformance
    from models.technician_bonus import TechnicianBonus
    
    # Inventory & Parts
    from models.part import Part
    from models.repair_part import RepairPart
    from models.category import Category
    from models.price_history import PriceHistory
    from models.inventory_log import InventoryLog
    
    # Customer Financial
    from models.invoice import Invoice
    from models.invoice_item import InvoiceItem
    from models.payment import Payment
    from models.credit_note import CreditNote
    
    # Supplier Management
    from models.supplier import Supplier
    from models.supplier_invoice import SupplierInvoice
    from models.supplier_payment import SupplierPayment
    
    # Purchase Orders
    from models.purchase_order import PurchaseOrder
    from models.purchase_order_item import PurchaseOrderItem
    from models.purchase_return import PurchaseReturn
    from models.purchase_return_item import PurchaseReturnItem
    
    # Business Configuration
    from models.branch import Branch
    from models.business_settings import BusinessSettings


def initialize_database():
    """
    Initialize the database connection and load all models.
    
    This function performs the following:
    1. Establishes connection to the SQLite database
    2. Loads and registers all model classes
    3. Prepares the database for use
    
    The actual table creation is handled by the MigrationService,
    which should be called after this initialization.
    
    Note:
        This function uses `reuse_if_open=True` to allow multiple
        initialization calls without errors. This is useful during
        testing and development.
    
    Example:
        >>> from config.database import initialize_database
        >>> initialize_database()
        >>> # Database is now ready for use
        >>> # Run migrations next:
        >>> from services.migration_service import MigrationService
        >>> MigrationService().run_migrations()
    
    See Also:
        - services.migration_service.MigrationService: Handles schema migrations
        - models: Individual model definitions
    """

    # Get dynamic database path
    db_path = get_db_path()
    
    # Ensure directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize the database object if not already initialized
    if db.database is None:
        print(f"Initializing database at: {db_path}")
        db.init(db_path, pragmas=DB_PRAGMAS)
        
    # Connect to database (reuse existing connection if open)
    db.connect(reuse_if_open=True)
    
    # Load and register all models
    load_models()
    
    # Note: Table creation is handled by MigrationService
    # The migration system provides better control over schema changes
    # and allows for versioned database updates