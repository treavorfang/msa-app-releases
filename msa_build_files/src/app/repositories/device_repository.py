"""Device Repository - Device Data Access Layer.

This repository handles all database operations for Device entities.
Features include device lookup, search, soft deletion, and filtering.
"""

from datetime import datetime
from typing import Optional, List
from peewee import fn
from models.device import Device
from models.customer import Customer


class DeviceRepository:
    """Repository for Device data access operations."""
    
    def create(self, device_data: dict) -> Device:
        """Create a new device."""
        return Device.create(**device_data)
    
    def get(self, device_id: int, include_deleted: bool = False) -> Optional[Device]:
        """Get device by ID with eager-loaded customer."""
        try:
            # Optimize with eager loading
            query = Device.select(Device, Customer).join(Customer)
            if not include_deleted:
                query = query.where(Device.is_deleted == False)
            return query.where(Device.id == device_id).get()
        except Device.DoesNotExist:
            return None
    
    def update(self, device_id: int, update_data: dict) -> Optional[Device]:
        """Update device with new values."""
        try:
            device = Device.select().where(Device.id == device_id).first()
            if not device:
                return None
            for key, value in update_data.items():
                setattr(device, key, value)
            device.save()
            return device
        except Device.DoesNotExist:
            return None
    
    def delete(self, device_id: int) -> bool:
        """Soft delete a device."""
        try:
            device = Device.select().where(Device.id == device_id).first()
            if not device:
                return False
            device.is_deleted = True
            device.deleted_at = datetime.now()
            device.save()
            return True
        except Device.DoesNotExist:
            return False
    
    def restore(self, device_id: int) -> bool:
        """Restore a soft-deleted device."""
        try:
            device = Device.select().where(Device.id == device_id).first()
            if not device:
                return False
            device.is_deleted = False
            device.deleted_at = None
            device.save()
            return True
        except Device.DoesNotExist:
            return False
    
    def list_all(self, filters: dict = None) -> List[Device]:
        """Get all devices with optional filtering.
        
        Args:
            filters (dict, optional): Dictionary containing filter criteria:
                - status: Device status
                - brand: Device brand
                - model: Device model
                - customer_id: ID of the customer
                - include_deleted: Boolean to include deleted devices
        """
        # Eager load Customer to avoid N+1
        query = Device.select(Device, Customer).join(Customer)
        
        if filters:
            # status filter
            if "status" in filters and filters["status"]:
                query = query.where(Device.status == filters["status"])

            # brand filter
            if "brand" in filters and filters["brand"]:
                query = query.where(Device.brand == filters["brand"])

            # model filter
            if "model" in filters and filters["model"]:
                query = query.where(Device.model == filters["model"])

            # customer filter
            if "customer_id" in filters and filters["customer_id"]:
                query = query.where(Device.customer == filters["customer_id"])

            # include_deleted filter
            include_deleted = filters.get("include_deleted", False)
            if not include_deleted:
                query = query.where(Device.is_deleted == False)

        return list(query.order_by(Device.received_at.desc()))
    
    def search(self, search_term: str, include_deleted: bool = False) -> List[Device]:
        """Search devices by barcode, brand, model, serial, or IMEI.
        
        Args:
            search_term (str): Term to search for
            include_deleted (bool): Whether to include soft-deleted devices
        """
        search_term = search_term.lower()
        # Search also benefits from eager load if we display customer info in search results
        query = Device.select(Device, Customer).join(Customer).where(
            (fn.LOWER(Device.barcode).contains(search_term)) |
            (fn.LOWER(Device.brand).contains(search_term)) | 
            (fn.LOWER(Device.model).contains(search_term)) |
            (fn.LOWER(Device.serial_number).contains(search_term)) |
            (fn.LOWER(Device.imei).contains(search_term))
        )
        if not include_deleted:
            query = query.where(Device.is_deleted == False)
        return list(query.order_by(Device.received_at.desc()))