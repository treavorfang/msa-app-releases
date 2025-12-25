from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from peewee import fn, prefetch
from dtos.invoice_create_request import InvoiceCreateRequest, PaymentRequest


from models.invoice import Invoice
from models.payment import Payment
from models.invoice_item import InvoiceItem
from models.part import Part
from models.device import Device
from models.customer import Customer
from models.user import User

router = APIRouter()

@router.get("/")
async def list_invoices(
    limit: int = 20, 
    skip: int = 0, 
    search: Optional[str] = None,
    customer_id: Optional[int] = None
):
    """
    List invoices with pagination and optional filtering using Repository.
    """
    try:
        from repositories.invoice_repository import InvoiceRepository
        repo = InvoiceRepository()
        
        invoices = repo.list_all(limit=limit, offset=skip, search=search, customer_id=customer_id)
        
        results = []
        for inv in invoices:
            # Calculate Paid Amount
            paid_amount = sum(float(p.amount) for p in inv.payments)
            total = float(inv.total)
            balance = max(0.0, total - paid_amount)
            
            # Robustly get customer name
            customer_name = "Walk-in"
            if inv.device and inv.device.customer:
                customer_name = inv.device.customer.name
                
            results.append({
                "id": inv.id,
                "number": inv.invoice_number,
                "date": inv.created_at.strftime("%Y-%m-%d"),
                "total": total,
                "paid": paid_amount,
                "balance": balance,
                "is_paid": inv.payment_status == 'paid',
                "status": inv.payment_status,
                "customer": customer_name
            })
            
        return results
    except Exception as e:
        print(f"Error listing invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/from-ticket/{ticket_id}")
async def create_invoice_from_ticket(ticket_id: int, req: Optional[InvoiceCreateRequest] = None):
    """
    Create a new invoice from a completed ticket.
    Supports optional checkout parameters via body:
    - labor_override: Manually set labor cost
    - payment: Initial payment (method, amount)
    """
    try:
        from services.ticket_service import TicketService
        from services.repair_part_service import RepairPartService
        from services.invoice_service import InvoiceService
        from services.payment_service import PaymentService
        from services.audit_service import AuditService
        from models.invoice import Invoice
        from models.invoice_item import InvoiceItem
        from config.constants import InvoiceNumbering
        
        # Initialize services
        audit_service = AuditService()
        ticket_service = TicketService(audit_service)
        part_service = RepairPartService(audit_service)
        invoice_service = InvoiceService(audit_service)
        payment_service = PaymentService(audit_service)
        
        ticket = ticket_service.get_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
            
        # Check if invoice already exists
        existing = (Invoice
                   .select()
                   .join(InvoiceItem)
                   .where(
                       (InvoiceItem.item_type == 'service') & 
                       (InvoiceItem.item_id == ticket_id)
                   )
                   .first())
                   
        if existing:
             return {"id": existing.id, "message": "Invoice already exists"}
             
        # Generate Invoice Number
        branch_id = 1
        if ticket.branch_id:
            branch_id = ticket.branch_id

        max_id_query = Invoice.select(fn.MAX(Invoice.id)).scalar() or 0
        new_seq = (max_id_query % 9999) + 1
        
        date_str = datetime.now().strftime(InvoiceNumbering.DATE_FORMAT)
        inv_num = InvoiceNumbering.FULL_FORMAT.format(
            prefix=InvoiceNumbering.PREFIX,
            branch_id=branch_id,
            date=date_str,
            sequence=InvoiceNumbering.SEQUENCE_FORMAT.format(new_seq)
        )
        
        # Calculate totals
        parts = part_service.get_parts_used_in_ticket(ticket_id)
        
        items = []
        parts_total = 0
        
        # 1. Parts (Apply 50% Markup)
        for p in parts:
            cost = p.part_price or 0
            unit_price = cost * 1.5 
            line_total = unit_price * p.quantity
            parts_total += line_total
            
            items.append({
                "item_type": "part",
                "item_id": p.part_id,
                "description": p.part_name,
                "sku": p.part_sku,
                "quantity": p.quantity,
                "unit_price": unit_price,
                "total": line_total
            })
            
        # 2. Labor Calculation
        labor_cost = 0.0
        
        if req and req.labor_override is not None:
            # User Manual Override
            labor_cost = req.labor_override
        else:
            # Auto-calculate: Total - Parts
            ticket_total_cost = float(ticket.actual_cost or ticket.estimated_cost or 0)
            labor_cost = max(0.0, ticket_total_cost - parts_total)
        
        # Add Service Item
        items.append({
            "item_type": "service",
            "item_id": ticket.id,
            "description": f"Service for Ticket #{ticket.ticket_number or ticket.id}",
            "quantity": 1,
            "unit_price": labor_cost,
            "total": labor_cost
        })
        
        final_total = parts_total + labor_cost
        
        # Resolve Customer ID
        customer_id = None
        if ticket.customer:
            customer_id = ticket.customer.id
        elif ticket.device and ticket.device.customer:
            customer_id = ticket.device.customer.id
            
        if not customer_id:
             raise HTTPException(status_code=400, detail="Ticket has no associated customer")

        # Prepare Invoice Data
        inv_data = {
            "invoice_number": inv_num,
            "customer": customer_id,
            "device": ticket.device_id,
            "subtotal": final_total,
            "tax": 0,
            "total": final_total,
            "payment_status": "unpaid",
            "due_date": datetime.now()
        }
        
        new_inv = invoice_service.create_invoice(inv_data, items)
        
        # 3. Handle Deposit
        deposit = float(ticket.deposit_paid or 0)
        current_paid = 0.0
        
        if deposit > 0:
            payment_service.create_payment({
                "invoice": new_inv.id,
                "amount": min(deposit, final_total),
                "payment_method": "deposit",
                "notes": f"Deposit transferred from Ticket #{ticket.ticket_number}",
                "paid_at": datetime.now()
            })
            current_paid += min(deposit, final_total)
            
        # 4. Handle Checkout Payment (New)
        if req and req.payment:
            pay_amt = req.payment.amount
            if pay_amt > 0:
                payment_service.create_payment({
                    "invoice": new_inv.id,
                    "amount": pay_amt,
                    "payment_method": req.payment.method,
                    "notes": req.payment.notes or "Mobile Checkout Payment",
                    "paid_at": datetime.now()
                })
                current_paid += pay_amt
                
        # 5. Update Ticket Actual Cost & Device Status
        ticket_service.update_ticket(ticket.id, {'actual_cost': final_total})
        
        if ticket.device and ticket.device.status != 'returned':
             from models.device import Device
             Device.update(status='returned').where(Device.id == ticket.device.id).execute()
        
        return {
            "id": new_inv.id, 
            "message": "Invoice created successfully",
            "total": final_total,
            "paid": current_paid,
            "status": "paid" if current_paid >= final_total else "partially_paid"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{invoice_id}/payments")
async def add_invoice_payment(invoice_id: int, payment_data: PaymentRequest):
    """
    Add a payment to an existing invoice.
    """
    try:
        from services.payment_service import PaymentService
        from services.audit_service import AuditService
        
        audit_service = AuditService()
        payment_service = PaymentService(audit_service)
        
        inv = Invoice.get_or_none(Invoice.id == invoice_id)
        if not inv:
             raise HTTPException(status_code=404, detail="Invoice not found")
             
        if inv.payment_status == 'paid':
             return {"message": "Invoice is already fully paid"}
             
        # Create Payment
        payment_service.create_payment({
            "invoice": inv.id,
            "amount": payment_data.amount,
            "payment_method": payment_data.method,
            "notes": payment_data.notes or "Mobile Payment",
            "paid_at": datetime.now()
        })
        
        return {"message": "Payment added successfully", "id": inv.id}
        
    except Exception as e:
        print(f"Error adding payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{invoice_id}")
async def get_invoice_detail(invoice_id: int):
    """
    Get full details of an invoice including line items.
    """
    try:
        inv = Invoice.get_or_none(Invoice.id == invoice_id)
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
            
        # Hydrate Customer/Device Logic
        customer = None
        device_name = "N/A"
        
        # 1. Try from direct Invoice -> Device -> Customer link
        if inv.device:
             device_name = f"{inv.device.brand} {inv.device.model}"
             if inv.device.customer:
                customer = inv.device.customer
        
        # 2. Fallback: Look for Ticket link in items if customer missing
        if not customer:
            for item in inv.items:
                if item.item_type == 'service':
                    # Assuming item_id is ticket_id for service items
                    from models.ticket import Ticket
                    t = Ticket.get_or_none(Ticket.id == item.item_id)
                    if t and t.device:
                         if device_name == "N/A":
                             device_name = f"{t.device.brand} {t.device.model}"
                         if t.device.customer:
                             customer = t.device.customer
                             break
        
        # Format Customer Data
        customer_data = {
            "name": "Walk-in",
            "phone": "N/A",
            "address": ""
        }
        if customer:
            customer_data = {
                "name": customer.name,
                "phone": customer.phone or "N/A",
                "address": customer.address or ""
            }
            
        # Process Items (InvoiceItem has NO description, must fetch from Source)
        items = []
        for item in inv.items:
            description = "Unknown Item"
            sku = ""
            
            if item.item_type == 'part':
                part = Part.get_or_none(Part.id == item.item_id)
                if part:
                    description = part.name
                    sku = part.sku
                else:
                    description = f"Part #{item.item_id} (Deleted)"
                    
            elif item.item_type == 'service':
                # Fetch ticket to get nice description
                from models.ticket import Ticket
                t = Ticket.get_or_none(Ticket.id == item.item_id)
                if t:
                    description = f"Service for Ticket #{t.ticket_number}"
                else:
                     description = "Service Charge"
            
            items.append({
                "description": description,
                "sku": sku,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
                "total": float(item.total)
            })

        items_data = items
            
        payments_data = []
        for p in inv.payments:
            payments_data.append({
                "amount": float(p.amount),
                "method": p.payment_method,
                "date": p.paid_at.strftime("%Y-%m-%d") if p.paid_at else ""
            })

        return {
            "id": inv.id,
            "number": inv.invoice_number,
            "created_at": inv.created_at.isoformat(),
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "status": inv.payment_status,
            "customer": customer_data,
            "device": device_name,
            "subtotal": float(inv.subtotal or 0),
            "tax": float(inv.tax or 0),
            "discount": float(inv.discount or 0),
            "total": float(inv.total or 0),
            "items": items_data,
            "payments": payments_data
        }
            
    except Exception as e:
        print(f"Error fetching invoice {invoice_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{invoice_id}/print")
async def print_invoice(invoice_id: int):
    """Trigger silent invoice print on the desktop printer."""
    try:
        from services.business_settings_service import BusinessSettingsService
        from services.audit_service import AuditService
        from utils.print.invoice_generator import InvoiceGenerator
        from models.invoice import Invoice
        
        # 1. Fetch invoice and settings
        inv = Invoice.get_by_id(invoice_id)
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
            
        audit_service = AuditService()
        settings_service = BusinessSettingsService(audit_service)
        
        # 2. Prepare item data
        items_data = []
        from models.part import Part
        from models.ticket import Ticket
        
        for item in inv.items:
            # Resolve Description
            description = "Unknown Item"
            if item.item_type == 'part':
                part = Part.get_or_none(Part.id == item.item_id)
                if part:
                    description = part.name
                else:
                    description = f"Part #{item.item_id}"
            elif item.item_type == 'service':
                t = Ticket.get_or_none(Ticket.id == item.item_id)
                if t:
                    description = f"Service for Ticket #{t.ticket_number}"
                else:
                    description = "Service Charge"
            else:
                description = item.description or "Item" # Fallback if model changes
            
            # Handle potential None values safely
            unit_price = float(item.unit_price or 0)
            total = float(item.total or 0)
            
            items_data.append({
                "description": description,
                "quantity": item.quantity or 1,
                "unit_price": unit_price,
                "total": total
            })
            
        # 3. Prepare print data
        # Calculate paid amount
        paid_amount = sum(float(p.amount or 0) for p in inv.payments)
        
        # Get ticket info safely
        ticket_num = ""
        device_name = ""
        issue = ""
        deposit = 0.0
        
        # Try to resolve ticket from items
        ticket = None
        for item in inv.items:
            if item.item_type == 'service':
                ticket = Ticket.get_or_none(Ticket.id == item.item_id)
                if ticket:
                    break
                    
        if ticket:
            ticket_num = ticket.ticket_number
            # Check if device relation exists
            if ticket.device:
                device_name = f"{ticket.device.brand} {ticket.device.model}"
            else:
                device_name = "Unknown Device"
            issue = ticket.error
            deposit = float(ticket.deposit_paid or 0)
        elif inv.device:
            device_name = f"{inv.device.brand} {inv.device.model}"
            
        # Get customer data
        customer_name = "Cash Customer"
        cust_phone = ""
        
        # Invoices are linked to customer via Device
        if inv.device and inv.device.customer:
            customer_name = inv.device.customer.name
            cust_phone = inv.device.customer.phone
            
        print_data = {
            'print_format': 'Standard A5', # Default for mobile trigger
            'invoice_number': inv.invoice_number,
            'date': inv.created_at.strftime("%Y-%m-%d"),
            'customer_name': customer_name,
            'customer_phone': cust_phone,
            'ticket_number': ticket_num,
            'device': device_name,
            'issue': issue,
            'items': items_data,
            'subtotal': float(inv.subtotal or 0),
            'tax': float(inv.tax or 0),
            'discount': float(inv.discount or 0),
            'total': float(inv.total or 0),
            'amount_paid': paid_amount,
            'deposit_paid': deposit
        }
        
        # 4. Trigger generator (Silent Mode)
        generator = InvoiceGenerator(business_settings_service=settings_service)
        generator.print_invoice(print_data, printer_name=None, silent=True)
        
        return {"status": "success", "message": "Print job sent to desktop printer"}
    except Exception as e:
        print(f"Print Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
