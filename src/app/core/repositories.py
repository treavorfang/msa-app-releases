# src/app/core/repositories.py
from repositories.user_repository import UserRepository
from repositories.role_repository import RoleRepository
from repositories.ticket_repository import TicketRepository
from repositories.device_repository import DeviceRepository
from repositories.part_repository import PartRepository
from repositories.repair_part_repository import RepairPartRepository
from repositories.category_repository import CategoryRepository
from repositories.supplier_repository import SupplierRepository
from repositories.branch_repository import BranchRepository
from repositories.business_settings_repository import BusinessSettingsRepository
from repositories.invoice_repository import InvoiceRepository
from repositories.invoice_item_repository import InvoiceItemRepository
from repositories.payment_repository import PaymentRepository
from repositories.purchase_order_repository import PurchaseOrderRepository
from repositories.warranty_repository import WarrantyRepository
from repositories.work_log_repository import WorkLogRepository
from repositories.technician_repository import TechnicianRepository
from repositories.purchase_return_repository import PurchaseReturnRepository
from repositories.purchase_return_item_repository import PurchaseReturnItemRepository
from repositories.credit_note_repository import CreditNoteRepository
from repositories.financial_repository import FinancialRepository

class Repositories:
    def __init__(self):
        """Initialize all repositories"""
        self._user_repository = UserRepository()
        self._role_repository = RoleRepository()
        self._ticket_repository = TicketRepository()
        self._device_repository = DeviceRepository()
        self._part_repository = PartRepository()
        self._repair_part_repository = RepairPartRepository()
        self._category_repository = CategoryRepository()
        self._supplier_repository = SupplierRepository()
        self._branch_repository = BranchRepository()
        self._business_settings_repository = BusinessSettingsRepository()
        self._invoice_repository = InvoiceRepository()
        self._invoice_item_repository = InvoiceItemRepository()
        self._payment_repository = PaymentRepository()
        self._purchase_order_repository = PurchaseOrderRepository()
        self._warranty_repository = WarrantyRepository()
        self._work_log_repository = WorkLogRepository()
        self._technician_repository = TechnicianRepository()
        self._purchase_return_repository = PurchaseReturnRepository()
        self._purchase_return_item_repository = PurchaseReturnItemRepository()
        self._purchase_return_item_repository = PurchaseReturnItemRepository()
        self._credit_note_repository = CreditNoteRepository()
        self._financial_repository = FinancialRepository()

    # Repository Properties
    @property
    def user_repository(self):
        return self._user_repository
    
    @property
    def role_repository(self):
        return self._role_repository
    
    @property
    def ticket_repository(self):
        return self._ticket_repository
    
    @property
    def device_repository(self):
        return self._device_repository
    
    @property
    def part_repository(self):
        return self._part_repository
    
    @property
    def repair_part_repository(self):
        return self._repair_part_repository
    
    @property
    def category_repository(self):
        return self._category_repository
    
    @property
    def supplier_repository(self):
        return self._supplier_repository
    
    @property
    def branch_repository(self):
        return self._branch_repository
    
    @property
    def business_settings_repository(self):
        return self._business_settings_repository
    
    @property
    def invoice_repository(self):
        return self._invoice_repository
    
    @property
    def invoice_item_repository(self):
        return self._invoice_item_repository
    
    @property
    def payment_repository(self):
        return self._payment_repository
    
    @property
    def purchase_order_repository(self):
        return self._purchase_order_repository
    
    @property
    def warranty_repository(self):
        return self._warranty_repository
    
    @property
    def work_log_repository(self):
        return self._work_log_repository
    
    @property
    def technician_repository(self):
        return self._technician_repository
    
    @property
    def purchase_return_repository(self):
        return self._purchase_return_repository
    
    @property
    def purchase_return_item_repository(self):
        return self._purchase_return_item_repository
    
    @property
    def credit_note_repository(self):
        return self._credit_note_repository
        
    @property
    def financial_repository(self):
        return self._financial_repository