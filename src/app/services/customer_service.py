"""CustomerService - Customer Management Business Logic.

This service handles all business operations related to customers,
including creation, updates, deletion (soft), restoration, and search.
It integrates with the AuditService to log all critical actions.
"""

from typing import List, Optional
from datetime import datetime
from repositories.customer_repository import CustomerRepository
from models.customer import Customer
from models.user import User
from services.audit_service import AuditService
from interfaces.icustomer_service import ICustomerService
from dtos.customer_dto import CustomerDTO


class CustomerService(ICustomerService):
    """Service class for Customer operations."""
    
    def __init__(self, repository: CustomerRepository = None, audit_service: AuditService = None):
        """Initialize CustomerService.
        
        Args:
            repository: Customer data access repository
            audit_service: Service for logging security/audit events
        """
        self.repository = repository or CustomerRepository()
        self.audit_service = audit_service or AuditService()
    
    def get_all_customers(self, limit: int = 20, offset: int = 0) -> List[CustomerDTO]:
        """Get all active customers as DTOs."""
        customers = self.repository.get_all(limit=limit, offset=offset)
        return [CustomerDTO.from_model(customer) for customer in customers]
    
    def get_all_customers_including_deleted(self) -> List[CustomerDTO]:
        """Get all customers (including deleted) as DTOs."""
        customers = self.repository.get_all(include_deleted=True)
        return [CustomerDTO.from_model(customer) for customer in customers]
    
    def get_customer(self, customer_id: int) -> Optional[CustomerDTO]:
        """Get a specific active customer by ID."""
        customer = self.repository.get_by_id(customer_id)
        return CustomerDTO.from_model(customer) if customer else None
    
    def get_customer_including_deleted(self, customer_id: int) -> Optional[CustomerDTO]:
        """Get a specific customer by ID, even if deleted."""
        customer = self.repository.get_by_id(customer_id, include_deleted=True)
        return CustomerDTO.from_model(customer) if customer else None
    
    def create_customer(self, customer_dto: CustomerDTO) -> CustomerDTO:
        """Create a new customer from a DTO.
        
        Args:
            customer_dto: Data transfer object containing customer details
            
        Returns:
            CustomerDTO: The created customer with ID and timestamps
            
        Raises:
            ValueError: If customer name already exists
        """
        if self.customer_exists(customer_dto.name):
            raise ValueError(f"Customer with name '{customer_dto.name}' already exists")
        
        data = customer_dto.to_dict()
        data['created_at'] = datetime.now()
        data['updated_at'] = datetime.now()
        
        customer_model = self.repository.create(data)
        created_dto = CustomerDTO.from_model(customer_model)  # Convert model to DTO
        
        # Audit log creation
        user = User.get_by_id(customer_dto.created_by) if customer_dto.created_by else None
        self.audit_service.log_action(
            user=user,
            action="customer_create",
            table_name="customers",
            new_data=created_dto.to_audit_dict(),
            ip_address=None
        )
        
        return created_dto
    
    def update_customer(self, customer_id: int, customer_dto: CustomerDTO) -> bool:
        """Update an existing customer.
        
        Args:
            customer_id: ID of customer to update
            customer_dto: New data
            
        Returns:
            bool: True if update was successful
            
        Raises:
            ValueError: If customer not found
        """
        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found")
        
        # Store old data for audit log
        old_data = customer.to_audit_dict()
        
        data = customer_dto.to_dict()
        data['updated_at'] = datetime.now()
        
        rows_updated = self.repository.update(customer_id, data)
        
        if rows_updated:
            updated_customer = self.get_customer(customer_id)
            user = User.get_by_id(customer_dto.updated_by) if customer_dto.updated_by else None
            
            # Audit log update
            self.audit_service.log_action(
                user=user,
                action="update",
                table_name="customers",
                old_data=old_data,
                new_data=updated_customer.to_audit_dict() if updated_customer else {},
                ip_address=None
            )
            return True
        
        return False
    
    def delete_customer(self, customer_id: int, user_id: Optional[int] = None) -> int:
        """Soft delete a customer.
        
        Args:
            customer_id: ID to delete
            user_id: ID of user performing action
            
        Returns:
            int: Number of rows affected (1 for success, 0 for failure)
            
        Raises:
            ValueError: If customer not found
        """
        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found")
        
        # Get the user if user_id is provided
        user = User.get_by_id(user_id) if user_id else None
        
        rows_deleted = self.repository.delete(customer_id)
        
        if rows_deleted > 0:
            # Audit log deletion
            self.audit_service.log_action(
                user=user,
                action="customer_delete",
                table_name="customers",
                old_data=customer.to_audit_dict(),
                ip_address=None
            )
            
            # Update the deleted_by field if user is provided
            if user_id:
                Customer.update(
                    updated_by=user_id,
                    updated_at=datetime.now()
                ).where(Customer.id == customer_id).execute()
        
        return rows_deleted
    
    def restore_customer(self, customer_id: int, user_id: Optional[int] = None) -> bool:
        """Restore a soft-deleted customer.
        
        Args:
            customer_id: ID of customer to restore
            user_id: ID of user performing the restoration
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If customer not found or not deleted
        """
        try:
            # Get the customer (including deleted ones)
            customer_model = self.repository.get_by_id(customer_id, include_deleted=True)
            if not customer_model:
                raise ValueError(f"Customer with ID {customer_id} not found")
            
            if not customer_model.deleted_at:
                raise ValueError(f"Customer with ID {customer_id} is not deleted")
            
            # Restore the customer
            rows_updated = self.repository.restore(customer_id)
            
            if rows_updated:
                # Convert to DTO for audit logging
                customer_dto = CustomerDTO.from_model(customer_model)
                
                # Audit log restoration
                user = User.get_by_id(user_id) if user_id else None
                self.audit_service.log_action(
                    user=user,
                    action="customer_restore",
                    table_name="customers",
                    new_data=customer_dto.to_audit_dict(),
                    ip_address=None
                )
                return True
            
            return False
            
        except Exception as e:
            # Re-raise exceptions to be handled by controller/UI
            if isinstance(e, ValueError):
                raise
            raise Exception(f"Failed to restore customer with ID {customer_id}: {str(e)}")
    
    def search_customers(self, query: str) -> List[CustomerDTO]:
        """Search customers by name, phone, or email."""
        customers = self.repository.search(query)
        return [CustomerDTO.from_model(customer) for customer in customers]
    
    def customer_exists(self, name: str) -> bool:
        """Check if a customer name already exists."""
        return self.repository.exists(name)