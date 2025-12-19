"""
Dependency Injection Container for MSA Application.

This module provides a centralized dependency injection container that manages
the lifecycle and dependencies of all services, repositories, and controllers
in the application.

The container uses a layered architecture:
- Core Services: Fundamental services (audit, roles, monitoring)
- Repositories: Data access layer
- Business Services: Business logic layer
- Controllers: Presentation layer coordination

All dependencies are lazily initialized and accessed through properties.
"""

from services.settings_service import SettingsService
from controllers.theme_controller import ThemeController

# Import layered components
from .core_services import CoreServices
from .repositories import Repositories
from .business_services import BusinessServices
from .controllers import Controllers


class DependencyContainer:
    """
    Central dependency injection container for the MSA application.
    
    This container manages all application dependencies using a layered
    architecture pattern. Dependencies are organized into four layers:
    
    1. Core Services - System-level services (audit, roles, monitoring)
    2. Repositories - Data access objects
    3. Business Services - Business logic implementation
    4. Controllers - UI coordination and request handling
    
    All dependencies are exposed as properties for lazy initialization
    and easy access throughout the application.
    
    Attributes:
        _app: Qt application instance
        _theme_controller: Theme management controller
        _core_services: Core services layer
        _repositories: Repository layer
        _business_services: Business services layer
        _controllers: Controller layer
        settings_service: User settings service
    
    Example:
        >>> container = DependencyContainer(app)
        >>> ticket_service = container.ticket_service
        >>> tickets = ticket_service.get_all_tickets()
    """
    
    def __init__(self, app=None):
        """
        Initialize the dependency container.
        
        Sets up all layers of the application architecture and initializes
        core services. The initialization order is important:
        1. Core services (no dependencies)
        2. Repositories (no dependencies)
        3. Business services (depend on core services and repositories)
        4. Controllers (depend on business services)
        
        Args:
            app: Qt QApplication instance (optional)
        """
        # Store app reference
        self._app = app
        
        # Initialize theme controller (requires app)
        self._theme_controller = ThemeController(app) if app else None
        
        # Initialize layered components in dependency order
        self._core_services = CoreServices()
        self._repositories = Repositories()
        self._business_services = BusinessServices(
            self._core_services,
            self._repositories
        )
        self._controllers = Controllers(self)
        
        # Initialize settings service
        self.settings_service = SettingsService()
    
    # ==================== Application Properties ====================
    
    @property
    def app(self):
        """Qt QApplication instance."""
        return self._app
    
    @property
    def theme_controller(self):
        """Theme management controller."""
        return self._theme_controller
    
    # ==================== Core Services Properties ====================
    
    @property
    def audit_service(self):
        """Audit logging service for tracking user actions."""
        return self._core_services.audit_service
    
    @property
    def role_service(self):
        """Role and permission management service."""
        return self._core_services.role_service
    
    @property
    def system_monitor_service(self):
        """System health and performance monitoring service."""
        return self._core_services.system_monitor_service
    
    # ==================== Repository Properties ====================
    
    @property
    def user_repository(self):
        """User data access repository."""
        return self._repositories.user_repository
    
    @property
    def role_repository(self):
        """Role data access repository."""
        return self._repositories.role_repository
    
    @property
    def ticket_repository(self):
        """Ticket data access repository."""
        return self._repositories.ticket_repository
    
    @property
    def device_repository(self):
        """Device data access repository."""
        return self._repositories.device_repository
    
    @property
    def part_repository(self):
        """Part/inventory data access repository."""
        return self._repositories.part_repository
    
    @property
    def repair_part_repository(self):
        """Repair part association data access repository."""
        return self._repositories.repair_part_repository
    
    @property
    def category_repository(self):
        """Category data access repository."""
        return self._repositories.category_repository
    
    @property
    def supplier_repository(self):
        """Supplier data access repository."""
        return self._repositories.supplier_repository
    
    @property
    def branch_repository(self):
        """Branch data access repository."""
        return self._repositories.branch_repository
    
    @property
    def business_settings_repository(self):
        """Business settings data access repository."""
        return self._repositories.business_settings_repository
    
    @property
    def invoice_repository(self):
        """Invoice data access repository."""
        return self._repositories.invoice_repository
    
    @property
    def invoice_item_repository(self):
        """Invoice item data access repository."""
        return self._repositories.invoice_item_repository
    
    @property
    def payment_repository(self):
        """Payment data access repository."""
        return self._repositories.payment_repository
    
    @property
    def purchase_order_repository(self):
        """Purchase order data access repository."""
        return self._repositories.purchase_order_repository
    
    @property
    def warranty_repository(self):
        """Warranty data access repository."""
        return self._repositories.warranty_repository
    
    @property
    def work_log_repository(self):
        """Work log data access repository."""
        return self._repositories.work_log_repository
    
    @property
    def technician_repository(self):
        """Technician data access repository."""
        return self._repositories.technician_repository
    
    # ==================== Business Services Properties ====================
    
    @property
    def auth_service(self):
        """Authentication and authorization service."""
        return self._business_services.auth_service
    
    @property
    def customer_service(self):
        """Customer management service."""
        return self._business_services.customer_service
    
    @property
    def ticket_service(self):
        """Ticket/repair management service."""
        return self._business_services.ticket_service
    
    @property
    def device_service(self):
        """Device management service."""
        return self._business_services.device_service
    
    @property
    def part_service(self):
        """Part/inventory management service."""
        return self._business_services.part_service
    
    @property
    def repair_part_service(self):
        """Repair part association service."""
        return self._business_services.repair_part_service
    
    @property
    def category_service(self):
        """Category management service."""
        return self._business_services.category_service
    
    @property
    def supplier_service(self):
        """Supplier management service."""
        return self._business_services.supplier_service
    
    @property
    def branch_service(self):
        """Branch management service."""
        return self._business_services.branch_service
    
    @property
    def business_settings_service(self):
        """Business settings management service."""
        return self._business_services.business_settings_service
    
    @property
    def invoice_service(self):
        """Invoice management service."""
        return self._business_services.invoice_service
    
    @property
    def invoice_item_service(self):
        """Invoice item management service."""
        return self._business_services.invoice_item_service
    
    @property
    def payment_service(self):
        """Payment processing service."""
        return self._business_services.payment_service
    
    @property
    def purchase_order_service(self):
        """Purchase order management service."""
        return self._business_services.purchase_order_service
    
    @property
    def purchase_return_service(self):
        """Purchase return management service."""
        return self._business_services.purchase_return_service
    
    @property
    def warranty_service(self):
        """Warranty management service."""
        return self._business_services.warranty_service
    
    @property
    def work_log_service(self):
        """Work log tracking service."""
        return self._business_services.work_log_service
    
    @property
    def technician_service(self):
        """Technician management service."""
        return self._business_services.technician_service
    
    @property
    def technician_performance_service(self):
        """Technician performance management service."""
        return self._business_services.technician_performance_service
    
    @property
    def supplier_invoice_service(self):
        """Supplier invoice management service."""
        return self._business_services.supplier_invoice_service
    
    @property
    def supplier_payment_service(self):
        """Supplier payment processing service."""
        return self._business_services.supplier_payment_service
    
    @property
    def report_service(self):
        """Report generation service."""
        return self._business_services.report_service
    
    @property
    def credit_note_service(self):
        """Credit note management service."""
        return self._business_services.credit_note_service
    
    # ==================== Controller Properties ====================
    
    @property
    def customer_controller(self):
        """Customer UI controller."""
        return self._controllers.customer_controller
    
    @property
    def ticket_controller(self):
        """Ticket UI controller."""
        return self._controllers.ticket_controller
    
    @property
    def device_controller(self):
        """Device UI controller."""
        return self._controllers.device_controller
    
    @property
    def job_controller(self):
        """Job UI controller."""
        return self._controllers.job_controller
    
    @property
    def inventory_controller(self):
        """Inventory UI controller."""
        return self._controllers.inventory_controller
    
    @property
    def report_controller(self):
        """Report UI controller."""
        return self._controllers.report_controller
    
    @property
    def setting_controller(self):
        """Settings UI controller."""
        return self._controllers.setting_controller
    
    @property
    def part_controller(self):
        """Part UI controller."""
        return self._controllers.part_controller
    
    @property
    def repair_part_controller(self):
        """Repair part UI controller."""
        return self._controllers.repair_part_controller
    
    @property
    def category_controller(self):
        """Category UI controller."""
        return self._controllers.category_controller
    
    @property
    def supplier_controller(self):
        """Supplier UI controller."""
        return self._controllers.supplier_controller
    
    @property
    def branch_controller(self):
        """Branch UI controller."""
        return self._controllers.branch_controller
    
    @property
    def business_settings_controller(self):
        """Business settings UI controller."""
        return self._controllers.business_settings_controller
    
    @property
    def invoice_controller(self):
        """Invoice UI controller."""
        return self._controllers.invoice_controller
    
    @property
    def invoice_item_controller(self):
        """Invoice item UI controller."""
        return self._controllers.invoice_item_controller
    
    @property
    def payment_controller(self):
        """Payment UI controller."""
        return self._controllers.payment_controller
    
    @property
    def purchase_order_controller(self):
        """Purchase order UI controller."""
        return self._controllers.purchase_order_controller
    
    @property
    def warranty_controller(self):
        """Warranty UI controller."""
        return self._controllers.warranty_controller
    
    @property
    def work_log_controller(self):
        """Work log UI controller."""
        return self._controllers.work_log_controller
    
    @property
    def technician_controller(self):
        """Technician UI controller."""
        return self._controllers.technician_controller
    
    @property
    def purchase_return_controller(self):
        """Purchase return UI controller."""
        return self._controllers.purchase_return_controller
    
    @property
    def technician_bonus_controller(self):
        """Technician bonus UI controller."""
        return self._controllers.technician_bonus_controller
    
    @property
    def technician_performance_controller(self):
        """Technician performance UI controller."""
        return self._controllers.technician_performance_controller


# Global container instance (deprecated - use dependency injection instead)
# container = DependencyContainer()