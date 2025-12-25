from fastapi import APIRouter, HTTPException, File, UploadFile, Header, Depends
from pydantic import BaseModel
from typing import List, Optional, Union
import os
from datetime import datetime
from models.ticket import Ticket
from models.ticket_photo import TicketPhoto
from models.device import Device
from models.user import User
from models.technician import Technician
from services.audit_service import AuditService
from services.repair_part_service import RepairPartService
from services.part_service import PartService
from services.ticket_service import TicketService
from config.constants import TicketStatus, TicketPriority

audit_service = AuditService()
part_service = PartService(audit_service)
repair_part_service = RepairPartService(audit_service, part_service)
ticket_service = TicketService(audit_service)

router = APIRouter()

async def get_current_user(
    x_user_id: Optional[int] = Header(None, alias="X-User-ID"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role")
) -> Optional[User]:
    """
    Helper to get user from headers.
    Unified: Always returns a User object (Technicians are now Users).
    """
    # print(f"DEBUG: get_current_user headers - ID: {x_user_id}, Role: {x_user_role}")
    if not x_user_id:
        return None
        
    try:
        # Always fetch from User table
        return User.get_by_id(x_user_id)
    except Exception:
        return None
    return None

class TicketCreate(BaseModel):
    device_id: int
    error: str
    error_description: Optional[str] = ""
    priority: str = "medium"
    estimated_cost: float = 0.0
    deposit_paid: float = 0.0
    internal_notes: Optional[str] = ""
    accessories: Optional[str] = ""

class TicketPartAdd(BaseModel):
    part_id: int
    quantity: int = 1
    notes: Optional[str] = None
    priority: str = "medium"
    estimated_cost: float = 0.0
    deposit_paid: float = 0.0
    internal_notes: Optional[str] = ""
    accessories: Optional[str] = ""

class TicketPartAdd(BaseModel):
    part_id: int
    quantity: int = 1
    notes: Optional[str] = None

@router.get("/")
async def get_tickets(
    tech_id: Optional[int] = None, 
    mode: str = "all",
    limit: int = 20, 
    skip: int = 0
):
    """
    Get list of tickets via Service.
    Supports modes: active, history, returned, all.
    """
    filters = {
        'limit': limit,
        'offset': skip
    }
    if tech_id:
        filters['technician_id'] = tech_id
        
    if mode == "active":
        filters['exclude_returned'] = True
        # Everything EXCEPT completed and cancelled
        filters['status'] = [s for s in TicketStatus.ALL if s not in [TicketStatus.COMPLETED, TicketStatus.CANCELLED]]
    elif mode == "history":
        filters['exclude_returned'] = True
        filters['status'] = [TicketStatus.COMPLETED, TicketStatus.CANCELLED]
    elif mode == "returned":
        filters['status'] = TicketStatus.ALL # Any status
        filters['only_returned'] = True
        
    tickets = ticket_service.list_tickets(filters)
    
    # Sort is now handled in repository (Created At Desc)
    # Tickets are pre-sorted by DB, but we might want custom priority logic still?
    # The mobile view relied on specific custom sorting: (Priority, CreatedAt).
    # The Repo now does CreatedAt.
    # To keep mobile complexity low, DB sorting by CreatedAt is often "good enough" for pagination.
    # However, if we strongly need Priority sort, we can't easily do it across pages efficiently without DB change.
    # For now, let's Stick to DB CreatedAt DESC as it's stable for pagination.
    
    
    results = []
    for t in tickets:
        results.append({
            "id": t.id,
            "number": t.ticket_number,
            "device": t.device_name,
            "status": t.status,
            "device_status": t.device_status,
            "priority": t.priority,
            "error": t.error,
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else ""
        })
    return results

@router.get("/{ticket_id}")
async def get_ticket_detail(ticket_id: int):
    """Get detailed information for a specific ticket via Service."""
    t = ticket_service.get_ticket(ticket_id)
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    
    # Correctly fetch invoice via InvoiceItem linkage
    from models.invoice import Invoice
    from models.invoice_item import InvoiceItem
    
    invoice_id = None
    try:
        invoice = (Invoice
                   .select()
                   .join(InvoiceItem)
                   .where(
                       (InvoiceItem.item_type == 'service') & 
                       (InvoiceItem.item_id == t.id)
                   )
                   .first())
        if invoice:
            invoice_id = invoice.id
    except Exception:
        pass

    return {
        "id": t.id,
        "number": t.ticket_number,
        "device": {
            "brand": t.brand,
            "model": t.model,
            "serial": t.serial_number,
            "imei": t.imei,
            "color": t.color,
            "condition": t.condition
        },
        "customer": t.customer_name,
        "status": t.status,
        "priority": t.priority,
        "error": t.error,
        "description": t.error_description,
        "estimated_cost": float(t.estimated_cost),
        "deposit": float(t.deposit_paid),
        "internal_notes": t.internal_notes,
        "device_status": t.device_status,
        "assigned_technician_id": t.assigned_technician_id,
        "assigned_technician_name": t.technician_name,
        "total_parts_cost": sum((p.part_price or 0) * p.quantity for p in repair_part_service.get_parts_used_in_ticket(ticket_id)),
        "created_at": t.created_at.isoformat() if hasattr(t.created_at, 'isoformat') else t.created_at,
        "invoice_id": invoice_id,
        "photos": [
            {
                "id": p.id,
                "url": f"/photos/{ticket_id}/{os.path.basename(p.image_path)}",
                "type": p.photo_type,
                "created_at": p.created_at.isoformat() if hasattr(p.created_at, 'isoformat') else str(p.created_at)
            } for p in t.photos
        ]
    }

@router.get("/lookup/{query}")
async def lookup_ticket(query: str):
    """
    Unified lookup for scanned codes via Service.
    Handles:
    - Ticket Number (RPT-...)
    - Ticket ID (123)
    - Invoice Number (INV-...)
    - QR Prefixes (TICKET:..., INVOICE:...)
    """
    search_q = query
    
    # Fast extraction for QR codes
    if search_q.startswith("INVOICE:"):
        search_q = search_q.replace("INVOICE:", "")
    elif search_q.startswith("TICKET:"):
        search_q = search_q.replace("TICKET:", "")
    
    # Search via TicketService (now includes IMEI/Serial)
    results = ticket_service.search_tickets(search_q)
    if results:
        return {"id": results[0].id}
        
    # Try as direct ID
    if search_q.isdigit():
        t = ticket_service.get_ticket(int(search_q))
        if t: return {"id": t.id}
        
    # Resolve via Invoice if search_q matches an invoice number
    from models.invoice import Invoice
    from models.ticket import Ticket
    inv = Invoice.select().where(Invoice.invoice_number == search_q).first()
    if inv:
        # Get latest ticket for this device
        latest_t = Ticket.select().where(Ticket.device == inv.device).order_by(Ticket.created_at.desc()).first()
        if latest_t: return {"id": latest_t.id}

    raise HTTPException(status_code=404, detail="No matching ticket found")

class StatusUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    actual_cost: Optional[float] = None
    assigned_technician_id: Optional[int] = None
    estimated_cost: Optional[float] = None

@router.patch("/{ticket_id}/status")
async def update_status(ticket_id: int, update: StatusUpdate, user: Optional[Union[User, Technician]] = Depends(get_current_user)):
    """Update ticket status and add internal notes."""
    print(f"DEBUG: update_status for ticket {ticket_id} by user {user}")
    try:
        t_dto = ticket_service.get_ticket(ticket_id)
        if not t_dto:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # 1. Update status if changed (this handles status history, device sync, and ending work logs)
        if update.status and update.status != t_dto.status:
            ticket_service.change_ticket_status(
                ticket_id=ticket_id,
                new_status=update.status,
                reason=f"Mobile Update: {update.notes}" if update.notes else "Status changed via mobile app",
                current_user=user,
                ip_address="Mobile App"
            )

        # 2. Update technician if changed (this handles work log automation)
        if update.assigned_technician_id is not None and update.assigned_technician_id != t_dto.assigned_technician_id:
            ticket_service.assign_ticket(
                ticket_id=ticket_id,
                technician_id=update.assigned_technician_id,
                reason="Assigned via mobile app",
                current_user=user,
                ip_address="Mobile App"
            )

        # 3. Update other fields (notes, costs)
        update_data = {}
        if update.notes:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            new_note = f"[{timestamp}] Mobile Update: {update.notes}"
            update_data['internal_notes'] = (t_dto.internal_notes or "") + f"\n{new_note}"
            
        if update.actual_cost is not None:
            update_data['actual_cost'] = update.actual_cost
        
        if update.estimated_cost is not None:
            update_data['estimated_cost'] = update.estimated_cost

        if update_data:
            ticket_service.update_ticket(
                ticket_id=ticket_id,
                update_data=update_data,
                current_user=user,
                ip_address="Mobile App"
            )
        
        # Get final state
        final_ticket = ticket_service.get_ticket(ticket_id)
        return {"status": "success", "new_status": final_ticket.status}
    except Exception as e:
        print(f"ERROR: update_status failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{ticket_id}/photos")
async def upload_photo(ticket_id: int, file: UploadFile = File(...), photo_type: str = "general"):
    """Hande photo upload for a ticket (e.g., Before/After proof)."""
    try:
        t = Ticket.get_by_id(ticket_id)
    except Ticket.DoesNotExist:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    # Define storage path
    storage_root = os.path.join(os.getcwd(), "User_Data", "Ticket_Photos")
    ticket_dir = os.path.join(storage_root, str(ticket_id))
    os.makedirs(ticket_dir, exist_ok=True)
    
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{photo_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
    full_path = os.path.join(ticket_dir, filename)
    
    # Save file
    with open(full_path, "wb") as buffer:
        buffer.write(await file.read())
        
    # Save to database record
    # Store relative path for portability
    relative_path = os.path.join("User_Data", "Ticket_Photos", str(ticket_id), filename)
    
    TicketPhoto.create(
        ticket=t,
        image_path=relative_path,
        photo_type=photo_type
    )
    
    return {"status": "success", "filename": filename, "path": relative_path}

@router.post("/")
async def create_ticket(req: TicketCreate, user: Optional[Union[User, Technician]] = Depends(get_current_user)):
    """Create a new repair ticket."""
    try:
        # Prepare data for TicketService
        ticket_data = {
            'device': req.device_id,
            'created_by': user.id if user and hasattr(user, 'id') else None,
            'status': "open",
            'priority': req.priority,
            'error': req.error,
            'error_description': req.error_description,
            'estimated_cost': req.estimated_cost,
            'deposit_paid': req.deposit_paid,
            'internal_notes': f"Mobile Create: {req.internal_notes}" if req.internal_notes else "Created via Mobile"
        }
        
        # Use TicketService (handles device status reset, auditing, etc.)
        ticket_dto = ticket_service.create_ticket(
            ticket_data=ticket_data,
            current_user=user,
            ip_address="Mobile App"
        )
        
        return {
            "status": "success",
            "ticket_id": ticket_dto.id,
            "ticket_number": ticket_dto.ticket_number
        }
    except Exception as e:
        print(f"ERROR: create_ticket failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ticket_id}/parts")
async def get_ticket_parts(ticket_id: int):
    """Get list of parts used in this ticket."""
    parts = repair_part_service.get_parts_used_in_ticket(ticket_id)
    return [{
        "id": p.id,
        "part_id": p.part_id,
        "name": p.part_name,
        "sku": p.part_sku,
        "quantity": p.quantity,
        "price": p.part_price,
        "total": (p.part_price or 0) * p.quantity
    } for p in parts]

@router.post("/{ticket_id}/parts")
async def add_ticket_part(ticket_id: int, req: TicketPartAdd, user: Optional[Union[User, Technician]] = Depends(get_current_user)):
    """Record usage of a part for a ticket."""
    try:
        repair_part = repair_part_service.create_repair_part(
            ticket_id=ticket_id,
            part_id=req.part_id,
            technician_id=user.id if user and hasattr(user, 'id') else None,
            current_user=user,
            quantity=req.quantity,
            notes=req.notes
        )
        return {"status": "success", "id": repair_part.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"ERROR: add_ticket_part failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{ticket_id}/parts/{item_id}")
async def remove_ticket_part(ticket_id: int, item_id: int, user: Optional[Union[User, Technician]] = Depends(get_current_user)):
    """Remove a part from a ticket and restore inventory."""
    success = repair_part_service.delete_repair_part(item_id, user=user)
    if not success:
        raise HTTPException(status_code=404, detail="Repair part record not found")
    return {"status": "success"}

@router.get("/{ticket_id}/history")
async def get_ticket_history(ticket_id: int):
    """Get combined status history and work logs for a ticket."""
    history = ticket_service.get_status_history(ticket_id)
    work_logs = ticket_service.get_work_logs(ticket_id)
    
    events = []
    
    # Add status history events
    for h in history:
        ts = h.changed_at.isoformat() if hasattr(h.changed_at, 'isoformat') else str(h.changed_at)
        
        # Robustly get name from User OR Technician model
        by_name = "System"
        if h.changed_by:
            # Check if it's a User object
            if hasattr(h.changed_by, 'username'): 
                by_name = getattr(h.changed_by, 'full_name', h.changed_by.username)
            # Check if it's a Technician object (or similar)
            elif hasattr(h.changed_by, 'name'):
                by_name = h.changed_by.name
            # Fallback for ID only or dict
            else:
                by_name = str(h.changed_by)
            
            # If still default or ID, try to lookup generic name if possible?
            # Issue: Peewee might return the ID if the FK is loose, or the object.
            # If it returns ID 1, it might look like Admin. 
            # If current_user was passed as Tech object, Peewee might have saved ID.
            
        events.append({
            "type": "status_change",
            "timestamp": ts,
            "old": h.old_status or "unknown",
            "new": h.new_status or "unknown",
            "reason": h.reason,
            "by": by_name
        })
        
    # Add work log events
    for w in work_logs:
        ts = w.start_time.isoformat() if hasattr(w.start_time, 'isoformat') else str(w.start_time)
        ets = w.end_time.isoformat() if hasattr(w.end_time, 'isoformat') else (str(w.end_time) if w.end_time else None)
        
        # Robustly get technician name
        tech_name = "System"
        if w.technician:
            # New Schema: Technician has .user link
            if w.technician.user:
                tech_name = w.technician.user.full_name
            else:
                 # Fallback (migration transition)
                 tech_name = getattr(w.technician, 'full_name', 'Technician')
            
        events.append({
            "type": "work_log",
            "timestamp": ts,
            "end_time": ets,
            "work": w.work_performed,
            "by": tech_name
        })
        
    # Sort events by timestamp descending
    events.sort(key=lambda x: x['timestamp'] if x['timestamp'] else "", reverse=True)
    return events
@router.post("/{ticket_id}/print")
async def print_ticket(ticket_id: int):
    """Trigger silent ticket print on the desktop printer."""
    try:
        from services.business_settings_service import BusinessSettingsService
        from utils.print.ticket_generator import TicketReceiptGenerator
        
        # 1. Fetch ticket and settings
        t_dto = ticket_service.get_ticket(ticket_id)
        if not t_dto:
            raise HTTPException(status_code=404, detail="Ticket not found")
            
        settings_service = BusinessSettingsService(audit_service)
        
        # 2. Prepare print data 
        # (Mirroring UI logic from ticket_details_dialog.py)
        print_data = {
            'print_format': 'Standard A5', # Default for mobile trigger
            'customer_name': t_dto.customer_name or "N/A",
            'customer_phone': getattr(t_dto, 'customer_phone', "N/A"),
            'customer_email': getattr(t_dto, 'customer_email', "N/A"),
            'customer_address': getattr(t_dto, 'customer_address', "N/A"),
            'brand': t_dto.brand or "",
            'model': t_dto.model or "",
            'imei': t_dto.imei or "",
            'serial_number': t_dto.serial_number or "",
            'color': t_dto.color or "",
            'condition': t_dto.condition or "",
            'passcode': t_dto.passcode or "",
            'issue_type': t_dto.error or "N/A",
            'description': t_dto.error_description or t_dto.error or "N/A",
            'accessories': getattr(t_dto, 'accessories', ""),
            'deadline': t_dto.deadline.strftime("%Y-%m-%d") if hasattr(t_dto, 'deadline') and t_dto.deadline else "N/A",
            'estimated_cost': t_dto.estimated_cost or 0.0,
            'deposit_paid': t_dto.deposit_paid or 0.0,
            'ticket_number': t_dto.ticket_number
        }
        
        # 3. Trigger generator (Silent Mode)
        generator = TicketReceiptGenerator(business_settings_service=settings_service)
        generator.print_ticket(print_data, printer_name=None, silent=True) # Silent mode bypasses dialog
        
        return {"status": "success", "message": "Print job sent to desktop printer"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Composite / Transactional Models
class CompositeCustomerData(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class CompositeDeviceData(BaseModel):
    id: Optional[int] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    imei: Optional[str] = None
    color: Optional[str] = None
    lock_type: Optional[str] = None
    passcode: Optional[str] = None

class CompositeTicketDetails(BaseModel):
    error: str
    error_description: Optional[str] = ""
    priority: str = "medium"
    estimated_cost: float = 0.0
    deposit_paid: float = 0.0
    internal_notes: Optional[str] = ""
    accessories: Optional[str] = ""

class CompositeTicketRequest(BaseModel):
    customer: CompositeCustomerData
    device: CompositeDeviceData
    ticket: CompositeTicketDetails

@router.post("/composite")
async def create_ticket_composite(req: CompositeTicketRequest, user: Optional[Union[User, Technician]] = Depends(get_current_user)):
    """
    Transactional Ticket Creation.
    Creates Customer (if new) -> Device (if new) -> Ticket in one atomic operation.
    """
    from config.database import db
    from services.customer_service import CustomerService
    from services.device_service import DeviceService
    
    # Init services locally to avoid circular deps if any
    cust_service = CustomerService(audit_service)
    dev_service = DeviceService(audit_service)

    try:
        with db.atomic():
            # 1. Handle Customer
            customer_id = req.customer.id
            if not customer_id:
                # Create New Customer
                if not req.customer.name:
                    raise HTTPException(status_code=400, detail="Customer name required for new customer")
                
                # Check duplication first
                if cust_service.customer_exists(req.customer.name):
                    # For mobile UX, if name exists, we usually try to find it or append something.
                    # But ideally we fail and tell user to select existing.
                    # However, strictly per user request: "save directly".
                    # Let's try to find it first? No, let's create it as per explicit new form.
                    # Actually, service raises ValueError if exists.
                    pass 

                c_dto = CustomerDTO(
                    name=req.customer.name,
                    phone=req.customer.phone,
                    email=req.customer.email,
                    created_by=user.id if user and hasattr(user, 'id') else None
                )
                created_cust = cust_service.create_customer(c_dto)
                customer_id = created_cust.id
            
            # 2. Handle Device
            device_id = req.device.id
            if not device_id:
                # Create New Device linked to customer_id
                if not req.device.brand or not req.device.model:
                     raise HTTPException(status_code=400, detail="Device brand and model required")
                
                d_data = {
                    "customer": customer_id,
                    "brand": req.device.brand,
                    "model": req.device.model,
                    "serial_number": req.device.serial,
                    "imei": req.device.imei,
                    "color": req.device.color,
                    "lock_type": req.device.lock_type,
                    "passcode": req.device.passcode,
                    "branch": 1 # Default branch
                }
                created_dev = dev_service.create_device(d_data, current_user=user, ip_address="Mobile App")
                device_id = created_dev.id
            
            # 3. Handle Ticket
            ticket_data = {
                'device': device_id,
                'created_by': user.id if user and hasattr(user, 'id') else None,
                'status': "open",
                'priority': req.ticket.priority,
                'error': req.ticket.error,
                'error_description': req.ticket.error_description,
                'estimated_cost': req.ticket.estimated_cost,
                'deposit_paid': req.ticket.deposit_paid,
                'internal_notes': f"Mobile Composite: {req.ticket.internal_notes}" if req.ticket.internal_notes else "Created via Mobile App"
            }
            
            if hasattr(req.ticket, 'accessories') and req.ticket.accessories: # Add accessories to ticket data if present in model/req
                 # Note: TicketCreate model defined earlier might not have accessories field explicitly?
                 # Let's check TicketCreate definition above. It doesn't have accessories.
                 # We need to add it to ticket_data manually if it's passed differently or update TicketCreate.
                 # The user wants accessories checkbox.
                 pass

            # Since TicketCreate model doesn't have 'accessories', we might need to rely on internal_notes or add it.
            # But the 'Ticket' model HAS 'accessories'. 
            # Let's inject it into ticket_data if we can pass it. 
            # See below for TicketCreate update.
            
            # Wait, I can't easily update TicketCreate struct in this replace block without replacing the whole file or multiple chunks.
            # I will access it from dynamic request if possible or I should have updated TicketCreate.
            # For now, let's assume 'internal_notes' carries it or we use a separate field in Composite Request if needed.
            # Better approach: Add 'accessories' to TicketCreate model in a separate edit or pass it in composite root.
            
            # Let's check `req.ticket`. It is `TicketCreate`.
            # I'll update TicketCreate model in a separate step. For now, I'll pass it if available.
             
            ticket_dto = ticket_service.create_ticket(
                ticket_data=ticket_data,
                current_user=user,
                ip_address="Mobile App"
            )
            
            # If we need to update accessories, we can do it post-create since create_ticket might not accept it in DTO conversion if strictly typed?
            # TicketService.create_ticket takes a dict.
            if hasattr(req.ticket, 'accessories'):
                 Ticket.update(accessories=req.ticket.accessories).where(Ticket.id == ticket_dto.id).execute()

            return {
                "status": "success",
                "ticket_id": ticket_dto.id,
                "ticket_number": ticket_dto.ticket_number,
                "customer_id": customer_id,
                "device_id": device_id
            }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"ERROR: create_ticket_composite failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/{ticket_id}/labor/start")
async def start_labor_timer(ticket_id: int, user: Optional[Union[User, Technician]] = Depends(get_current_user)):
    """Start a new labor timer for the technician."""
    from models.work_log import WorkLog
    
    # Check if a timer is already running for this tech on this ticket
    active_log = WorkLog.select().where(
        (WorkLog.ticket == ticket_id) & 
        (WorkLog.technician == user.id) & 
        (WorkLog.end_time.is_null())
    ).first()
    
    if active_log:
        return {"status": "error", "message": "Timer already running", "log_id": active_log.id}
    
    # Create new log
    log = WorkLog.create(
        ticket=ticket_id,
        technician=user.id,
        work_performed="Labor Timer Started",
        start_time=datetime.now()
    )
    return {"status": "success", "log_id": log.id, "start_time": log.start_time.isoformat()}

@router.post("/{ticket_id}/labor/stop")
async def stop_labor_timer(ticket_id: int, user: Optional[Union[User, Technician]] = Depends(get_current_user)):
    """Stop the active labor timer."""
    from models.work_log import WorkLog
    
    active_log = WorkLog.select().where(
        (WorkLog.ticket == ticket_id) & 
        (WorkLog.technician == user.id) & 
        (WorkLog.end_time.is_null())
    ).first()
    
    if not active_log:
        raise HTTPException(status_code=404, detail="No active timer found")
        
    active_log.end_time = datetime.now()
    active_log.work_performed = "Labor Timer Stopped (Mobile)"
    active_log.save()
    
    # Calculate duration
    duration = active_log.end_time - active_log.start_time
    minutes = round(duration.total_seconds() / 60)
    
    return {"status": "success", "duration_minutes": minutes}

@router.get("/{ticket_id}/labor/active")
async def get_active_timer(ticket_id: int, user: Optional[Union[User, Technician]] = Depends(get_current_user)):
    """Check if there is an active timer."""
    from models.work_log import WorkLog
    
    active_log = WorkLog.select().where(
        (WorkLog.ticket == ticket_id) & 
        (WorkLog.technician == user.id) & 
        (WorkLog.end_time.is_null())
    ).first()
    
    if active_log:
        return {
            "active": True, 
            "start_time": active_log.start_time.isoformat() if hasattr(active_log.start_time, 'isoformat') else str(active_log.start_time)
        }
    return {"active": False}

class DiagnosticsUpdate(BaseModel):
    results: dict # {"Screen": "Pass", "Battery": "Fail"}
    technician_notes: Optional[str] = None

@router.post("/{ticket_id}/diagnostics")
async def save_diagnostics(ticket_id: int, diag: DiagnosticsUpdate, user: Optional[Union[User, Technician]] = Depends(get_current_user)):
    """Append structured diagnostics to internal notes."""
    try:
        t = ticket_service.get_ticket(ticket_id)
        if not t:
            raise HTTPException(status_code=404, detail="Ticket not found")
            
        # Format diagnostics report
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        report = f"\n--- DIAGNOSTICS REPORT ({timestamp}) ---\n"
        for component, result in diag.results.items():
            report += f"[{result.upper()}] {component}\n"
            
        if diag.technician_notes:
            report += f"Notes: {diag.technician_notes}\n"
        report += "----------------------------------------\n"
        
        # Append to internal notes
        update_data = {
            'internal_notes': (t.internal_notes or "") + report
        }
        
        ticket_service.update_ticket(
            ticket_id=ticket_id,
            update_data=update_data,
            current_user=user,
            ip_address="Mobile App"
        )
        
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
