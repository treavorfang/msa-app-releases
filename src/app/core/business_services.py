# src/app/core/business_services.py
from services.auth_service import AuthService
from services.customer_service import CustomerService
from services.ticket_service import TicketService
from services.device_service import DeviceService
from services.part_service import PartService
from services.repair_part_service import RepairPartService
from services.category_service import CategoryService
from services.supplier_service import SupplierService
from services.branch_service import BranchService
from services.business_settings_service import BusinessSettingsService
from services.invoice_service import InvoiceService
from services.invoice_item_service import InvoiceItemService
from services.payment_service import PaymentService
from services.purchase_order_service import PurchaseOrderService
from services.purchase_return_service import PurchaseReturnService
from services.warranty_service import WarrantyService
from services.work_log_service import WorkLogService
from services.technician_service import TechnicianService
from services.technician_performance_service import TechnicianPerformanceService
from services.supplier_invoice_service import SupplierInvoiceService
from services.supplier_payment_service import SupplierPaymentService
from services.report_service import ReportService
from services.credit_note_service import CreditNoteService
from services.financial_service import FinancialService

from interfaces.iauth_service import IAuthService
from interfaces.icustomer_service import ICustomerService
from interfaces.iticket_service import ITicketService
from interfaces.idevice_service import IDeviceService
from interfaces.ipart_service import IPartService
from interfaces.irepair_part_service import IRepairPartService
from interfaces.icategory_service import ICategoryService
from interfaces.isupplier_service import ISupplierService
from interfaces.ibranch_service import IBranchService
from interfaces.ibusiness_settings_service import IBusinessSettingsService
from interfaces.iinvoice_service import IInvoiceService
from interfaces.iinvoice_item_service import IInvoiceItemService
from interfaces.ipayment_service import IPaymentService
from interfaces.ipurchase_order_service import IPurchaseOrderService
from interfaces.ipurchase_return_service import IPurchaseReturnService
from interfaces.iwarranty_service import IWarrantyService
from interfaces.iwork_log_service import IWorkLogService
from interfaces.itechnician_service import ITechnicianService
from interfaces.itechnician_performance_service import ITechnicianPerformanceService

class BusinessServices:
    def __init__(self, core_services, repositories):
        """Initialize services that depend on repositories or other services"""
        self._auth_service: IAuthService = AuthService(
            user_repository=repositories.user_repository,
            audit_service=core_services.audit_service,
            role_service=core_services.role_service
        )

        self._customer_service: ICustomerService = CustomerService(
            audit_service=core_services.audit_service
        )

        self._ticket_service: ITicketService = TicketService(
            audit_service=core_services.audit_service
        )

        self._device_service: IDeviceService = DeviceService(
            audit_service=core_services.audit_service
        )

        self._part_service: IPartService = PartService(
            audit_service=core_services.audit_service
        )

        self._repair_part_service: IRepairPartService = RepairPartService(
            audit_service=core_services.audit_service,
            part_service=self._part_service
        )

        self._category_service: ICategoryService = CategoryService(
            audit_service=core_services.audit_service
        )
        
        self._supplier_service: ISupplierService = SupplierService(
            audit_service=core_services.audit_service
        )

        self._branch_service: IBranchService = BranchService(
            audit_service=core_services.audit_service
        )

        self._business_settings_service: IBusinessSettingsService = BusinessSettingsService(
            audit_service=core_services.audit_service
        )

        self._invoice_service: IInvoiceService = InvoiceService(
            audit_service=core_services.audit_service
        )
        
        self._invoice_item_service: IInvoiceItemService = InvoiceItemService(
            audit_service=core_services.audit_service
        )
        
        self._payment_service: IPaymentService = PaymentService(
            audit_service=core_services.audit_service
        )

        self._purchase_order_service: IPurchaseOrderService = PurchaseOrderService(
            audit_service=core_services.audit_service,
            part_service=self._part_service
        )
        
        self._purchase_return_service: IPurchaseReturnService = PurchaseReturnService(
            audit_service=core_services.audit_service,
            part_service=self._part_service
        )

        self._warranty_service: IWarrantyService = WarrantyService(
            audit_service=core_services.audit_service
        )
        
        self._work_log_service: IWorkLogService = WorkLogService(
            audit_service=core_services.audit_service
        )

        self._technician_service: ITechnicianService = TechnicianService(
            audit_service=core_services.audit_service
        )
        
        self._technician_performance_service: ITechnicianPerformanceService = TechnicianPerformanceService()
        
        self._supplier_invoice_service = SupplierInvoiceService(
            audit_service=core_services.audit_service
        )
        
        self._supplier_payment_service = SupplierPaymentService(
            audit_service=core_services.audit_service
        )
        
        self._credit_note_service = CreditNoteService(
            audit_service=core_services.audit_service
        )
        
        self._report_service = ReportService()
        
        self._financial_service = FinancialService(
            repository=repositories.financial_repository,
            audit_service=core_services.audit_service
        )

    # Business Services Properties
    @property
    def auth_service(self) -> IAuthService:
        return self._auth_service

    @property
    def customer_service(self) -> ICustomerService:
        return self._customer_service
    
    @property
    def ticket_service(self) -> ITicketService:
        return self._ticket_service
    
    @property
    def device_service(self) -> IDeviceService:
        return self._device_service
    
    @property
    def part_service(self) -> IPartService:
        return self._part_service
    
    @property
    def repair_part_service(self) -> IRepairPartService:
        return self._repair_part_service
    
    @property
    def category_service(self) -> ICategoryService:
        return self._category_service
    
    @property
    def supplier_service(self) -> ISupplierService:
        return self._supplier_service
    
    @property
    def branch_service(self) -> IBranchService:
        return self._branch_service
    
    @property
    def business_settings_service(self) -> IBusinessSettingsService:
        return self._business_settings_service
    
    @property
    def invoice_service(self) -> IInvoiceService:
        return self._invoice_service
    
    @property
    def invoice_item_service(self) -> IInvoiceItemService:
        return self._invoice_item_service
    
    @property
    def payment_service(self) -> IPaymentService:
        return self._payment_service
    
    @property
    def purchase_order_service(self) -> IPurchaseOrderService:
        return self._purchase_order_service
        
    @property
    def purchase_return_service(self) -> IPurchaseReturnService:
        return self._purchase_return_service
    
    @property
    def warranty_service(self) -> IWarrantyService:
        return self._warranty_service
    
    @property
    def work_log_service(self) -> IWorkLogService:
        return self._work_log_service
    
    @property
    def technician_service(self) -> ITechnicianService:
        return self._technician_service
    
    @property
    def technician_performance_service(self) -> ITechnicianPerformanceService:
        return self._technician_performance_service
    
    @property
    def supplier_invoice_service(self):
        return self._supplier_invoice_service
    
    @property
    def supplier_payment_service(self):
        return self._supplier_payment_service
    
    @property
    def credit_note_service(self):
        return self._credit_note_service
    
    @property
    def report_service(self):
        return self._report_service
        
    @property
    def financial_service(self):
        return self._financial_service