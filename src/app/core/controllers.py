# src/app/core/controllers.py
from controllers.customer_controller import CustomerController
from controllers.ticket_controller import TicketController
from controllers.device_controller import DeviceController
from controllers.job_controller import JobController
from controllers.inventory_controller import InventoryController
from controllers.report_controller import ReportController
from controllers.setting_controller import SettingController
from controllers.part_controller import PartController
from controllers.repair_part_controller import RepairPartController
from controllers.category_controller import CategoryController
from controllers.supplier_controller import SupplierController
from controllers.branch_controller import BranchController
from controllers.business_settings_controller import BusinessSettingsController
from controllers.invoice_controller import InvoiceController
from controllers.invoice_item_controller import InvoiceItemController
from controllers.payment_controller import PaymentController
from controllers.purchase_order_controller import PurchaseOrderController
from controllers.warranty_controller import WarrantyController
from controllers.work_log_controller import WorkLogController
from controllers.technician_controller import TechnicianController
from controllers.purchase_return_controller import PurchaseReturnController
from controllers.technician_bonus_controller import TechnicianBonusController
from controllers.technician_performance_controller import TechnicianPerformanceController

class Controllers:
    def __init__(self, dependency_container):
        """Initialize all controllers"""
        self._customer_controller = CustomerController(dependency_container.customer_service)
        self._ticket_controller = TicketController(dependency_container)
        self._device_controller = DeviceController(dependency_container)
        self._job_controller = JobController(dependency_container)
        self._inventory_controller = InventoryController(dependency_container)
        self._report_controller = ReportController(dependency_container)
        self._setting_controller = SettingController(dependency_container)
        self._part_controller = PartController(dependency_container.part_service)
        self._repair_part_controller = RepairPartController(dependency_container.repair_part_service)
        self._category_controller = CategoryController(dependency_container)
        self._supplier_controller = SupplierController(dependency_container)
        self._branch_controller = BranchController(dependency_container)
        self._business_settings_controller = BusinessSettingsController(dependency_container)
        self._invoice_controller = InvoiceController(dependency_container)
        self._invoice_item_controller = InvoiceItemController(dependency_container)
        self._payment_controller = PaymentController(dependency_container)
        self._purchase_order_controller = PurchaseOrderController(dependency_container)
        self._warranty_controller = WarrantyController(dependency_container)
        self._work_log_controller = WorkLogController(dependency_container)
        self._technician_controller = TechnicianController(dependency_container)
        self._purchase_return_controller = PurchaseReturnController(dependency_container)
        self._technician_bonus_controller = TechnicianBonusController()
        self._technician_performance_controller = TechnicianPerformanceController(dependency_container)

    # Controller Properties
    @property
    def customer_controller(self):
        return self._customer_controller
    
    @property
    def ticket_controller(self):
        return self._ticket_controller
    
    @property
    def device_controller(self):
        return self._device_controller
    
    @property
    def job_controller(self):
        return self._job_controller
    
    @property
    def inventory_controller(self):
        return self._inventory_controller
    
    @property
    def report_controller(self):
        return self._report_controller
    
    @property
    def setting_controller(self):
        return self._setting_controller
    
    @property
    def part_controller(self):
        return self._part_controller
    
    @property
    def repair_part_controller(self):
        return self._repair_part_controller
    
    @property
    def category_controller(self):
        return self._category_controller
    
    @property
    def supplier_controller(self):
        return self._supplier_controller
    
    @property
    def branch_controller(self):
        return self._branch_controller
    
    @property
    def business_settings_controller(self):
        return self._business_settings_controller
    
    @property
    def invoice_controller(self):
        return self._invoice_controller
    
    @property
    def invoice_item_controller(self):
        return self._invoice_item_controller
    
    @property
    def payment_controller(self):
        return self._payment_controller
    
    @property
    def purchase_order_controller(self):
        return self._purchase_order_controller
    
    @property
    def warranty_controller(self):
        return self._warranty_controller
    
    @property
    def work_log_controller(self):
        return self._work_log_controller
    
    @property
    def technician_controller(self):
        return self._technician_controller
    
    @property
    def purchase_return_controller(self):
        return self._purchase_return_controller
    
    @property
    def technician_bonus_controller(self):
        return self._technician_bonus_controller
    
    @property
    def technician_performance_controller(self):
        return self._technician_performance_controller