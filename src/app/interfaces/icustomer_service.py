# interfaces/icustomer_service.py
from abc import ABC, abstractmethod
from typing import Optional, List
from dtos.customer_dto import CustomerDTO

class ICustomerService(ABC):
    """Interface defining the contract for customer services"""
    
    @abstractmethod
    def create_customer(self, customer_dto: CustomerDTO) -> CustomerDTO:
        """Creates a new customer with validation"""
        pass
    
    @abstractmethod
    def get_customer(self, customer_id: int) -> Optional[CustomerDTO]:
        """Retrieves a customer by ID"""
        pass
    
    @abstractmethod
    def get_customer_including_deleted(self, customer_id: int) -> Optional[CustomerDTO]:
        """Retrieves a customer by ID including deleted ones"""
        pass
        
    @abstractmethod
    def update_customer(self, customer_id: int, customer_dto: CustomerDTO) -> bool:
        """Updates customer details"""
        pass
        
    @abstractmethod
    def delete_customer(self, customer_id: int, user_id: Optional[int] = None) -> int:
        """Soft deletes a customer by ID"""
        pass
        
    @abstractmethod
    def get_all_customers(self) -> List[CustomerDTO]:
        """Returns all active customers"""
        pass
    
    @abstractmethod
    def get_all_customers_including_deleted(self) -> List[CustomerDTO]:
        """Returns all customers including deleted ones"""
        pass
        
    @abstractmethod
    def search_customers(self, query: str) -> List[CustomerDTO]:
        """Searches customers by query"""
        pass
        
    @abstractmethod
    def customer_exists(self, name: str) -> bool:
        """Checks if customer exists by name"""
        pass