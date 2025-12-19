# src/app/controllers/device_controller.py
from PySide6.QtCore import QObject, Signal
from models.device import Device
from dtos.device_dto import DeviceDTO  # Add this import
from typing import List, Optional
from core.event_bus import EventBus
from core.events import (
    DeviceCreatedEvent, DeviceUpdatedEvent, 
    DeviceDeletedEvent, DeviceRestoredEvent
)

class DeviceController(QObject):
    device_created = Signal(DeviceDTO)  # Changed to DTO
    device_updated = Signal(DeviceDTO)  # Changed to DTO
    device_deleted = Signal(int)
    device_restored = Signal(int)
    
    def __init__(self, container):
        super().__init__()
        self.container = container
        self.device_service = container.device_service
        
    def create_device(self, device_data: dict, current_user=None, ip_address=None) -> Optional[DeviceDTO]:
        device = self.device_service.create_device(device_data, current_user, ip_address)
        if device:
            self.device_created.emit(device)
            user_id = current_user.id if current_user else None
            EventBus.publish(DeviceCreatedEvent(device.id, user_id))
        return device
        
    def get_device(self, device_id: int) -> Optional[DeviceDTO]:
        return self.device_service.get_device(device_id)
        
    def get_device_including_deleted(self, device_id: int) -> Optional[DeviceDTO]:
        return self.device_service.get_device_including_deleted(device_id)
        
    def update_device(self, device_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[DeviceDTO]:
        device = self.device_service.update_device(device_id, update_data, current_user, ip_address)
        if device:
            self.device_updated.emit(device)
            user_id = current_user.id if current_user else None
            EventBus.publish(DeviceUpdatedEvent(device.id, user_id))
        return device
        
    def delete_device(self, device_id: int, current_user=None, ip_address=None) -> bool:
        success = self.device_service.delete_device(device_id, current_user, ip_address)
        if success:
            self.device_deleted.emit(device_id)
            self.container.customer_controller.data_changed.emit()
            user_id = current_user.id if current_user else None
            EventBus.publish(DeviceDeletedEvent(device_id, user_id))
        return success
        
    def restore_device(self, device_id: int, current_user=None, ip_address=None) -> bool:
        success = self.device_service.restore_device(device_id, current_user, ip_address)
        if success:
            self.device_restored.emit(device_id)
            self.container.customer_controller.data_changed.emit()
            user_id = current_user.id if current_user else None
            EventBus.publish(DeviceRestoredEvent(device_id, user_id))
        return success
        
    def list_devices(self, filters: dict = None) -> List[DeviceDTO]:
        return self.device_service.list_devices(filters)
        
    def search_devices(self, search_term: str) -> List[DeviceDTO]:
        return self.device_service.search_devices(search_term)