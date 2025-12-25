from fastapi import APIRouter
from services.device_service import DeviceService
from services.audit_service import AuditService

router = APIRouter()
audit_service = AuditService()
device_service = DeviceService(audit_service)

@router.get("/search")
async def search_devices(q: str):
    """Search devices by IMEI, brand, model, or serial."""
    devices = device_service.search_devices(q)
    return [{
        "id": d.id,
        "model": f"{d.brand or ''} {d.model or ''}".strip(),
        "imei": d.imei,
        "serial": d.serial_number,
        "customer": {
            "id": d.customer_id,
            "name": d.customer_name
        } if d.customer_id else None
    } for d in devices]
