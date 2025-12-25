
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
        for item in inv.items:
            # Handle potential None values safely
            unit_price = float(item.unit_price or 0)
            total = float(item.total or 0)
            
            items_data.append({
                "description": item.description or "Unknown Item",
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
        
        if inv.ticket:
            ticket_num = inv.ticket.ticket_number
            device_name = inv.ticket.device_name
            issue = inv.ticket.error
            deposit = float(inv.ticket.deposit_paid or 0)
            
        # Get customer phone
        cust_phone = ""
        if inv.customer:
            cust_phone = inv.customer.phone
            
        print_data = {
            'print_format': 'Standard A5', # Default for mobile trigger
            'invoice_number': inv.invoice_number,
            'date': inv.created_at.strftime("%Y-%m-%d"),
            'customer_name': inv.customer_name or "Cash Customer",
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
