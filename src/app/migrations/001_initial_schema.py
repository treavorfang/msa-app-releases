from config.database import db
# Import ALL models that existed at version 1
from models.role import Role
from models.permission import Permission
from models.role_permission import RolePermission
from models.user import User
from models.audit_log import AuditLog
from models.customer import Customer
from models.device import Device
from models.ticket import Ticket
from models.status_history import StatusHistory
from models.warranty import Warranty
from models.technician import Technician
from models.work_log import WorkLog
from models.part import Part
from models.repair_part import RepairPart
from models.invoice import Invoice
from models.invoice_item import InvoiceItem
from models.payment import Payment
from models.supplier import Supplier
from models.supplier_invoice import SupplierInvoice
from models.supplier_payment import SupplierPayment
from models.technician_performance import TechnicianPerformance
from models.technician_bonus import TechnicianBonus
from models.purchase_order import PurchaseOrder
from models.purchase_order_item import PurchaseOrderItem
from models.inventory_log import InventoryLog
from models.branch import Branch  
from models.business_settings import BusinessSettings
from models.category import Category
from models.price_history import PriceHistory
from models.purchase_return import PurchaseReturn
from models.purchase_return_item import PurchaseReturnItem
from models.credit_note import CreditNote

def apply(database):
    """Apply the initial schema"""
    tables = [
        Branch,  
        Role,
        Permission,
        RolePermission,
        User,
        AuditLog,
        Customer,
        Device,
        Supplier,
        Category,
        Part,
        Technician,
        Ticket,
        StatusHistory,
        Warranty,
        WorkLog,
        RepairPart,
        Invoice,
        InvoiceItem,
        Payment,
        PurchaseOrder,
        PurchaseOrderItem,
        InventoryLog,
        PriceHistory,
        SupplierInvoice,
        SupplierPayment,
        TechnicianPerformance,
        TechnicianBonus,
        PurchaseReturn,
        PurchaseReturnItem,
        CreditNote,
        BusinessSettings
    ]
    
    # safe=True treats this as distinct from 'initialize_database' so it won't crash 
    # if tables exist.
    database.create_tables(tables, safe=True)
    
    # Create default roles if they don't exist
    from services.role_service import RoleService
    from services.audit_service import AuditService
    
    # We can perform data seeding here too
    if Role.select().count() == 0:
        audit_service = AuditService()
        RoleService.create_default_roles(audit_service)
        print("Seeded default roles.")
        
    # Seed default branch
    if Branch.select().count() == 0:
        Branch.create(
            name="Main Branch",
            address="",
            phone=""
        )
        print("Seeded default branch: Main Branch")

def revert(database):
    """Revert is dangerous for initial schema, usually we drop tables"""
    pass
