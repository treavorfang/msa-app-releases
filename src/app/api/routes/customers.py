from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional, Union
from models.user import User
from models.technician import Technician
from services.customer_service import CustomerService
from services.device_service import DeviceService
from services.audit_service import AuditService
from dtos.customer_dto import CustomerDTO
from utils.validation.input_validator import InputValidator

router = APIRouter()
audit_service = AuditService()
customer_service = CustomerService(audit_service=audit_service)
device_service = DeviceService(audit_service=audit_service)

async def get_current_user(
    x_user_id: Optional[int] = Header(None, alias="X-User-ID"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role")
) -> Optional[Union[User, Technician]]:
    if not x_user_id or not x_user_role:
        return None
    try:
        if x_user_role == "staff":
            return User.get_by_id(x_user_id)
        elif x_user_role == "technician":
            return Technician.get_by_id(x_user_id)
    except Exception:
        return None
    return None

class CustomerCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None

class DeviceCreate(BaseModel):
    brand: str
    model: str
    serial: Optional[str] = None
    imei: Optional[str] = None
    color: Optional[str] = None

@router.post("/")
async def create_customer(req: CustomerCreate, user: Optional[Union[User, Technician]] = Depends(get_current_user)):
    """Create a new customer using Service (parity with Desktop)."""
    # Validation
    if req.phone and not InputValidator.validate_phone(req.phone):
        raise HTTPException(status_code=400, detail="Invalid phone number format")
    if req.email:
        is_valid, msg = InputValidator.validate_email(req.email)
        if not is_valid: raise HTTPException(status_code=400, detail=msg)

    try:
        dto = CustomerDTO(
            name=req.name,
            phone=req.phone,
            email=req.email,
            created_by=user.id if user and hasattr(user, 'id') else None
        )
        customer = customer_service.create_customer(dto)
        return {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{customer_id}/devices")
async def create_device(customer_id: int, req: DeviceCreate, user: Optional[Union[User, Technician]] = Depends(get_current_user)):
    """Create a new device for a customer using Service."""
    if req.imei and not InputValidator.validate_imei(req.imei):
        raise HTTPException(status_code=400, detail="Invalid IMEI number (checksum failed)")

    try:
        device_data = {
            "customer": customer_id,
            "brand": req.brand,
            "model": req.model,
            "serial_number": req.serial,
            "imei": req.imei,
            "color": req.color
        }
        device = device_service.create_device(
            device_data=device_data, 
            current_user=user,
            ip_address="Mobile App"
        )
        return {
            "id": device.id,
            "brand": device.brand,
            "model": device.model,
            "serial": device.serial_number
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
async def get_customers(limit: int = 20, skip: int = 0):
    """Get paginated list of customers via Service."""
    customers = customer_service.get_all_customers(limit=limit, offset=skip)
    
    return [{
        "id": c.id,
        "name": c.name,
        "phone": c.phone,
        "email": c.email
    } for c in customers]

@router.get("/search")
async def search_customers(q: str):
    """Search customers via Service."""
    customers = customer_service.search_customers(q)
    return [{
        "id": c.id,
        "name": c.name,
        "phone": c.phone,
        "email": c.email
    } for c in customers]

@router.get("/{customer_id}")
async def get_customer_detail(customer_id: int):
    """Get full customer details including devices and recent tickets."""
    customer = customer_service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    devices = device_service.list_devices(filters={'customer_id': customer_id})
    
    # Get recent tickets for this customer
    from services.ticket_service import TicketService
    ticket_service = TicketService()
    tickets = ticket_service.list_tickets(filters={'customer_id': customer_id})
    tickets.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
    
    return {
        "id": customer.id,
        "name": customer.name,
        "phone": customer.phone,
        "email": customer.email,
        "devices": [{
            "id": d.id,
            "brand": d.brand,
            "model": d.model,
            "serial": d.serial_number
        } for d in devices],
        "recent_tickets": [{
            "id": t.id,
            "number": t.ticket_number,
            "device": t.device_name,
            "status": t.status,
            "created_at": t.created_at.strftime("%Y-%m-%d") if t.created_at else ""
        } for t in tickets[:5]]
    }

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

@router.patch("/{customer_id}")
async def update_customer(customer_id: int, req: CustomerUpdate, user: Optional[Union[User, Technician]] = Depends(get_current_user)):
    """Update customer details."""
    current = customer_service.get_customer(customer_id)
    if not current:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    # Validation
    if req.phone and not InputValidator.validate_phone(req.phone):
        raise HTTPException(status_code=400, detail="Invalid phone format")
    if req.email:
        is_valid, msg = InputValidator.validate_email(req.email)
        if not is_valid: raise HTTPException(status_code=400, detail=msg)

    # Use DTO for update
    update_dto = CustomerDTO(
        id=customer_id,
        name=req.name or current.name,
        phone=req.phone if req.phone is not None else current.phone,
        email=req.email if req.email is not None else current.email,
        updated_by=user.id if user and hasattr(user, 'id') else None
    )
    
    success = customer_service.update_customer(customer_id, update_dto)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update customer")
        
    return {"status": "success"}

@router.get("/{customer_id}/devices")
async def get_customer_devices(customer_id: int):
    """Get all devices for a specific customer via Service."""
    devices = device_service.list_devices(filters={'customer_id': customer_id})
    return [{
        "id": d.id,
        "brand": d.brand,
        "model": d.model,
        "serial": d.serial_number
    } for d in devices]
@router.get("/devices/search")
async def search_devices(q: str):
    """Global search for devices by brand, model, serial, or IMEI."""
    devices = device_service.search_devices(q)
    return [{
        "id": d.id,
        "brand": d.brand,
        "model": d.model,
        "serial": d.serial_number,
        "imei": d.imei,
        "customer_id": d.customer.id if d.customer else None,
        "customer_name": d.customer.name if d.customer else "Unknown"
    } for d in devices]
