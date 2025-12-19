# src/app/controllers/customer_controller.py
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox
from typing import Optional, List
from services.customer_service import CustomerService
from services.audit_service import AuditService
from interfaces.icustomer_service import ICustomerService
from dtos.customer_dto import CustomerDTO
from dtos.device_dto import DeviceDTO
from dtos.device_dto import DeviceDTO
from views.customer.customer_form import CustomerForm
from core.event_bus import EventBus
from core.events import CustomerCreatedEvent, CustomerUpdatedEvent, CustomerDeletedEvent

class CustomerController(QObject):
    data_changed = Signal()
    
    def __init__(self, service: ICustomerService = None, audit_service: AuditService = None):
        super().__init__()
        self.service = service or CustomerService()
        self.audit_service = audit_service or AuditService()
    
    def get_all_customers(self) -> List[CustomerDTO]:
        try:
            return self.service.get_all_customers()
        except Exception as e:
            self._show_error("Failed to load customers", str(e))
            return []
    
    def get_all_customers_including_deleted(self) -> List[CustomerDTO]:
        try:
            return self.service.get_all_customers_including_deleted()
        except Exception as e:
            self._show_error("Failed to load customers", str(e))
            return []
    
    def get_customer(self, customer_id: int) -> Optional[CustomerDTO]:
        try:
            return self.service.get_customer(customer_id)
        except Exception as e:
            self._show_error("Failed to load customer", str(e))
            return None
    
    def get_customer_including_deleted(self, customer_id: int) -> Optional[CustomerDTO]:
        try:
            return self.service.get_customer_including_deleted(customer_id)
        except Exception as e:
            self._show_error("Failed to load customer", str(e))
            return None
    
    def create_customer(self, data: dict) -> Optional[CustomerDTO]:
        try:
            # Convert dict to DTO
            customer_dto = CustomerDTO(
                name=data.get('name', ''),
                phone=data.get('phone'),
                email=data.get('email'),
                address=data.get('address'),
                notes=data.get('notes'),
                preferred_contact_method=data.get('preferred_contact_method', 'phone'),
                created_by=data.get('created_by'),
                updated_by=data.get('updated_by')
            )
            
            customer = self.service.create_customer(customer_dto)
            if customer:
                self.data_changed.emit()
                EventBus.publish(CustomerCreatedEvent(customer.id, customer.created_by))
            return customer
        except Exception as e:
            self._show_error("Failed to create customer", str(e))
            return None
    
    def update_customer(self, customer_id: int, data: dict) -> bool:
        try:
            # Convert dict to DTO for update
            customer_dto = CustomerDTO(
                name=data.get('name', ''),
                phone=data.get('phone'),
                email=data.get('email'),
                address=data.get('address'),
                notes=data.get('notes'),
                preferred_contact_method=data.get('preferred_contact_method', 'phone'),
                updated_by=data.get('updated_by')
            )
            
            success = self.service.update_customer(customer_id, customer_dto)
            if success:
                self.data_changed.emit()
                EventBus.publish(CustomerUpdatedEvent(customer_id, customer_dto.updated_by))
            return success
        except Exception as e:
            self._show_error("Failed to update customer", str(e))
            return False
    
    def delete_customer(self, customer_id: int, user_id: Optional[int] = None):
        try:
            deleted = self.service.delete_customer(customer_id, user_id)
            if deleted > 0:
                self.data_changed.emit()
                EventBus.publish(CustomerDeletedEvent(customer_id, user_id))
                return True
            return False
        except Exception as e:
            self._show_error("Failed to delete customer", str(e))
            return False
        
    def restore_customer(self, customer_id: int, user_id: Optional[int] = None) -> bool:
        """
        Restore a deleted customer.
        Args:
            customer_id: ID of customer to restore
            user_id: ID of user performing the restoration
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            restored = self.service.restore_customer(customer_id, user_id)
            if restored:
                self.data_changed.emit()
            return restored
        except Exception as e:
            self._show_error("Failed to restore customer", str(e))
            return False
        
    def show_new_customer_form(self, user_id: int, parent=None):
        form = CustomerForm(self, user_id=user_id, parent=parent)
        form.setWindowTitle("Create New Customer")
        if form.exec():
            QMessageBox.information(parent, "Success", "Customer created successfully")

    def show_edit_customer_form(self, customer_id: int, user_id: int, parent=None):
        customer = self.service.get_customer(customer_id)
        if not customer:
            QMessageBox.warning(parent, "Error", "Customer not found")
            return
        
        form = CustomerForm(self, user_id=user_id, parent=parent)
        form.setWindowTitle("Edit Customer")
        form.customer_id = customer.id
        
        # Pre-populate form with existing customer data
        form.name_input.setText(customer.name)
        form.phone_input.setText(customer.phone)
        form.email_input.setText(customer.email or "")
        form.address_input.setText(customer.address or "")
        form.note_input.setText(customer.notes or "")
        
        # Set the contact method
        if customer.preferred_contact_method:
            index = form.contact_method.findText(customer.preferred_contact_method)
            if index >= 0:
                form.contact_method.setCurrentIndex(index)
        
        if form.exec():
            QMessageBox.information(parent, "Success", "Customer updated successfully")

    def search_customers(self, query: str) -> List[CustomerDTO]:
        try:
            return self.service.search_customers(query)
        except Exception as e:
            self._show_error("Search failed", str(e))
            return []
    
    def _show_error(self, title, message):
        QMessageBox.critical(None, title, message)

    def get_customer_devices(self, customer_id: int) -> List[DeviceDTO]:
        """Get all devices for a specific customer"""
        try:
            # Use the device service through the container
            if hasattr(self, 'container') and hasattr(self.container, 'device_controller'):
                return self.container.device_controller.list_devices(
                    {'customer_id': customer_id}
                )
            # Fallback: try to use device service directly
            elif hasattr(self, 'container') and hasattr(self.container, 'device_service'):
                return self.container.device_service.list_devices(
                    {'customer_id': customer_id}
                )
            else:
                # As a last resort, we could create a device service instance
                # But this should ideally be handled through dependency injection
                from services.device_service import DeviceService
                from services.audit_service import AuditService
                device_service = DeviceService(AuditService())
                return device_service.list_devices({'customer_id': customer_id})
        except Exception as e:
            self._show_error("Failed to load devices", str(e))
            return []