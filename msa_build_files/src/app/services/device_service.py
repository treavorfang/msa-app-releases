"""DeviceService - Device Management Business Logic.

This service handles all operations related to customer devices (phones, laptops, etc.).
It manages lifecycle (create, update, delete, restore) and integrates with audit logging.
"""

from typing import List, Optional, Dict, Any
from interfaces.idevice_service import IDeviceService
from repositories.device_repository import DeviceRepository
from models.device import Device
from dtos.device_dto import DeviceDTO
from services.audit_service import AuditService


class DeviceService(IDeviceService):
    """Service class for Device operations."""
    
    def __init__(self, audit_service: AuditService):
        """Initialize DeviceService.
        
        Args:
            audit_service: Service for logging security/audit events
        """
        self.repository = DeviceRepository()
        self.audit_service = audit_service
        
    def create_device(self, device_data: dict, current_user=None, ip_address=None) -> DeviceDTO:
        """Create a new device record.
        
        Args:
            device_data: Dictionary of device properties
            current_user: User creating the device (for audit)
            ip_address: Client IP (for audit)
            
        Returns:
            DeviceDTO: The created device
        """
        # Auto-assign to Main Branch (ID=1) if not specified
        if 'branch' not in device_data or device_data['branch'] is None:
            device_data['branch'] = 1
        
        device_model = self.repository.create(device_data)
        device_dto = DeviceDTO.from_model(device_model)
        
        self.audit_service.log_action(
            user=current_user,
            action="device_create",
            table_name="devices",
            new_data=device_dto.to_audit_dict(),
            ip_address=ip_address
        )
        return device_dto
        
    def get_device(self, device_id: int) -> Optional[DeviceDTO]:
        """Get an active device by ID."""
        device_model = self.repository.get(device_id)
        return DeviceDTO.from_model(device_model) if device_model else None
    
    def get_device_including_deleted(self, device_id: int) -> Optional[DeviceDTO]:
        """Get a device by ID, including if deleted."""
        device_model = self.repository.get(device_id, include_deleted=True)
        return DeviceDTO.from_model(device_model) if device_model else None
    
    def get_device_by_imei(self, imei: str) -> Optional[DeviceDTO]:
        """Get a device by its IMEI/Serial number."""
        device_model = Device.get_or_none(Device.imei == imei)
        return DeviceDTO.from_model(device_model) if device_model else None
        
    def update_device(self, device_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[DeviceDTO]:
        """Update an existing device.
        
        Args:
            device_id: ID to update
            update_data: New properties
            current_user: User performing update
            ip_address: Client IP
            
        Returns:
            Optional[DeviceDTO]: Updated device or None if not found
        """
        old_device_model = self.repository.get(device_id)
        if not old_device_model:
            return None
            
        old_device_dto = DeviceDTO.from_model(old_device_model)
        
        device_model = self.repository.update(device_id, update_data)
        if device_model:
            device_dto = DeviceDTO.from_model(device_model)
            
            self.audit_service.log_action(
                user=current_user,
                action="device_update",
                table_name="devices",
                old_data=old_device_dto.to_audit_dict(),
                new_data=device_dto.to_audit_dict(),
                ip_address=ip_address
            )
            return device_dto
        return None
        
    def delete_device(self, device_id: int, current_user=None, ip_address=None) -> bool:
        """Soft delete a device.
        
        Args:
            device_id: ID to delete
            current_user: User performing delete
            ip_address: Client IP
            
        Returns:
            bool: Success status
        """
        device_model = self.repository.get(device_id)
        if not device_model:
            return False
            
        device_dto = DeviceDTO.from_model(device_model)
        success = self.repository.delete(device_id)
        
        if success:
            self.audit_service.log_action(
                user=current_user,
                action="device_delete",
                table_name="devices",
                old_data=device_dto.to_audit_dict(),
                ip_address=ip_address
            )
        return success
        
    def restore_device(self, device_id: int, current_user=None, ip_address=None) -> bool:
        """Restore a soft-deleted device.
        
        Args:
            device_id: ID to restore
            current_user: User performing restore
            ip_address: Client IP
            
        Returns:
            bool: Success status
        """
        device_model = self.repository.get(device_id, include_deleted=True)
        if not device_model:
            return False
            
        device_dto = DeviceDTO.from_model(device_model)
        success = self.repository.restore(device_id)
        
        if success:
            self.audit_service.log_action(
                user=current_user,
                action="device_restore",
                table_name="devices",
                new_data=device_dto.to_audit_dict(),
                ip_address=ip_address
            )
        return success
        
    def list_devices(self, filters: dict = None) -> List[DeviceDTO]:
        """List devices with optional filtering."""
        device_models = self.repository.list_all(filters)
        return [DeviceDTO.from_model(device) for device in device_models]
        
    def search_devices(self, search_term: str) -> List[DeviceDTO]:
        """Search devices by IMEI, brand, model, or customer name."""
        device_models = self.repository.search(search_term)
        return [DeviceDTO.from_model(device) for device in device_models]