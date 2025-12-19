"""Customer Repository - Customer Data Access Layer.

This repository handles all database operations for Customer entities.
Includes optimized search, soft deletion, and customer management.
"""

import re
from functools import reduce
from operator import or_
from datetime import datetime
from typing import List, Optional
from peewee import DoesNotExist, fn
from models.customer import Customer


class CustomerRepository:
    """Repository for Customer data access operations."""
    
    def get_all(self, include_deleted: bool = False) -> List[Customer]:
        """Retrieve all customers ordered by name.
        
        Args:
            include_deleted (bool): Whether to include deleted customers
            
        Returns:
            List[Customer]: List of Customer objects
        """
        try:
            query = Customer.select().order_by(Customer.name)
            if not include_deleted:
                query = query.where(Customer.is_deleted == False)
            return list(query)
        except Exception as e:
            raise Exception(f"Failed to retrieve customers: {str(e)}")
    
    def get_by_id(self, customer_id: int, include_deleted: bool = False) -> Optional[Customer]:
        """Retrieve a customer by ID.
        
        Args:
            customer_id (int): Customer ID to retrieve
            include_deleted (bool): Whether to include deleted customers
        """
        try:
            query = Customer.select()
            if not include_deleted:
                query = query.where(Customer.is_deleted == False)
            return query.where(Customer.id == customer_id).get()
        except DoesNotExist:
            return None
        except Exception as e:
            raise Exception(f"Failed to retrieve customer with ID {customer_id}: {str(e)}")
    
    def create(self, data: dict) -> Customer:
        """Create a new customer.
        
        Args:
            data (dict): Dictionary containing customer attributes
        """
        try:
            return Customer.create(**data)
        except Exception as e:
            raise Exception(f"Failed to create customer: {str(e)}")
    
    def update(self, customer_id: int, data: dict) -> int:
        """Update an existing customer.
        
        Args:
            customer_id (int): ID of customer to update
            data (dict): Dictionary containing fields to update
            
        Returns:
            int: Number of rows updated (should be 1 if successful)
        """
        try:
            # Remove created_by if it exists in update data
            data.pop('created_by', None)
            
            data['updated_at'] = datetime.now()
            rows_updated = Customer.update(**data).where(Customer.id == customer_id).execute()
            if rows_updated == 0:
                raise DoesNotExist(f"Customer with ID {customer_id} not found")
            return rows_updated
        except DoesNotExist as e:
            raise
        except Exception as e:
            raise Exception(f"Failed to update customer with ID {customer_id}: {str(e)}")
    
    def search(self, query: str, limit: int = 100) -> List[Customer]:
        """Index-optimized search across customer fields.
        
        Searches across:
        - Name (using index)
        - Email (using index)
        - Phone (both formatted and unformatted)
        - Address
        
        Args:
            query: Search string
            limit: Maximum results to return
        """
        try:
            query = query.strip()
            if not query:
                return list(Customer.select().where(Customer.is_deleted == False).order_by(Customer.name))
                
            conditions = []
            query_lower = query.lower()
            
            # Name search (uses name index)
            if len(query) >= 2:
                conditions.append(Customer.name ** f"%{query}%")
            
            # Email search (uses email index)
            if "@" in query:
                conditions.append(Customer.email ** f"%{query_lower}%")
            
            # Phone search (uses phone index)
            if any(c.isdigit() for c in query):
                clean_phone = re.sub(r'[^\d+]', '', query)
                if clean_phone:
                    phone_conditions = []
                    # Search original phone field
                    phone_conditions.append(Customer.phone ** f"%{clean_phone}%")
                    # Search normalized phone
                    phone_conditions.append(
                        fn.REPLACE(
                            fn.REPLACE(Customer.phone, ' ', ''),
                            '-', ''
                        ) ** f"%{clean_phone}%"
                    )
                    conditions.append(reduce(or_, phone_conditions))
            
            # Address search (uses address index)
            if len(query) >= 3:
                conditions.append(Customer.address ** f"%{query}%")
            
            if conditions:
                base_condition = (Customer.is_deleted == False)
                query_obj = Customer.select().where(base_condition & reduce(or_, conditions))
                results = list(query_obj.order_by(Customer.name).limit(limit))
                return results
            return []
            
        except Exception as e:
            raise ValueError("Search failed due to an error") from e
    
    def delete(self, customer_id: int) -> int:
        """Soft delete a customer by ID.
        
        Returns:
            int: Number of rows updated
        """
        try:
            rows_updated = Customer.update(
                is_deleted=True,
                deleted_at=datetime.now()
            ).where(
                (Customer.id == customer_id) & 
                (Customer.is_deleted == False)
            ).execute()
            
            if rows_updated == 0:
                raise DoesNotExist(f"Customer with ID {customer_id} not found or already deleted")
            return rows_updated
        except DoesNotExist as e:
            raise
        except Exception as e:
            raise Exception(f"Failed to delete customer with ID {customer_id}: {str(e)}")
    
    def exists(self, name: str) -> bool:
        """Check if a customer with the given name exists."""
        try:
            return Customer.select().where(Customer.name == name).exists()
        except Exception as e:
            raise Exception(f"Failed to check customer existence: {str(e)}")
    
    def restore(self, customer_id: int) -> int:
        """Restore a soft-deleted customer."""
        try:
            rows_updated = Customer.update(
                is_deleted=False,
                deleted_at=None
            ).where(Customer.id == customer_id).execute()
            
            if rows_updated == 0:
                raise DoesNotExist(f"Customer with ID {customer_id} not found")
            return rows_updated
        except DoesNotExist as e:
            raise
        except Exception as e:
            raise Exception(f"Failed to restore customer with ID {customer_id}: {str(e)}")