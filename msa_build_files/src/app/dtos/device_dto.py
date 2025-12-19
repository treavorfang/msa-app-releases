# src/app/dtos/device_dto.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class DeviceDTO:
    id: Optional[int] = None
    brand: str = ""
    model: str = ""
    serial_number: Optional[str] = None
    imei: Optional[str] = None
    color: Optional[str] = None
    passcode: Optional[str] = None
    lock_type: Optional[str] = None
    condition: Optional[str] = None
    status: str = "received"
    barcode: Optional[str] = None
    branch_id: Optional[int] = None
    is_deleted: bool = False
    received_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    customer_id: Optional[int] = None
    deleted_at: Optional[datetime] = None
    customer_name: Optional[str] = None  # For UI display
    
    @classmethod
    def from_model(cls, device) -> 'DeviceDTO':
        """Convert Device model to DeviceDTO"""
        return cls(
            id=device.id,
            brand=device.brand,
            model=device.model,
            serial_number=device.serial_number,
            imei=device.imei,
            color=device.color,
            passcode=device.passcode,
            lock_type=device.lock_type if hasattr(device, 'lock_type') else None,
            condition=device.condition,
            status=device.status,
            barcode=device.barcode,
            branch_id=device.branch_id,
            is_deleted=device.is_deleted,
            received_at=device.received_at,
            completed_at=device.completed_at,
            customer_id=device.customer_id,
            deleted_at=device.deleted_at,
            customer_name=device.customer.name if device.customer else None
        )
    
    def to_dict(self) -> dict:
        """Convert DTO to dictionary for service/repository use"""
        return {
            'brand': self.brand,
            'model': self.model,
            'serial_number': self.serial_number,
            'imei': self.imei,
            'color': self.color,
            'passcode': self.passcode,
            'lock_type': self.lock_type,
            'condition': self.condition,
            'status': self.status,
            'barcode': self.barcode,
            'branch_id': self.branch_id,
            'customer_id': self.customer_id
        }
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging"""
        return {
            'device_id': self.id,
            'brand': self.brand,
            'model': self.model,
            'serial_number': self.serial_number,
            'imei': self.imei
        }