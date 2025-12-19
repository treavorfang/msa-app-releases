# src/app/interfaces/idevice_service.py
from abc import ABC, abstractmethod
from typing import List, Optional
from dtos.device_dto import DeviceDTO  # Add this import

class IDeviceService(ABC):
    @abstractmethod
    def create_device(self, device_data: dict) -> DeviceDTO:  # Changed return type
        pass
        
    @abstractmethod
    def get_device(self, device_id: int) -> Optional[DeviceDTO]:  # Changed return type
        pass
        
    @abstractmethod
    def update_device(self, device_id: int, update_data: dict) -> DeviceDTO:  # Changed return type
        pass
        
    @abstractmethod
    def delete_device(self, device_id: int) -> bool:
        pass
        
    @abstractmethod
    def list_devices(self, filters: dict = None) -> List[DeviceDTO]:  # Changed return type
        pass
        
    @abstractmethod
    def search_devices(self, search_term: str) -> List[DeviceDTO]:  # Changed return type
        pass
        
    @abstractmethod
    def restore_device(self, device_id: int) -> bool:
        """Restore a soft-deleted device"""
        pass
        
    @abstractmethod
    def get_device_including_deleted(self, device_id: int) -> Optional[DeviceDTO]:  # Added method
        pass
        
    @abstractmethod
    def get_device_by_imei(self, imei: str) -> Optional[DeviceDTO]:  # Changed return type
        pass