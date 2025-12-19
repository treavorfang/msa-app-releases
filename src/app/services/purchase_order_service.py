"""PurchaseOrderService - Procurement Business Logic.

This service manages purchase orders using DTOs.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from interfaces.ipurchase_order_service import IPurchaseOrderService
from repositories.purchase_order_repository import PurchaseOrderRepository
from repositories.purchase_order_item_repository import PurchaseOrderItemRepository
from models.purchase_order import PurchaseOrder
from models.purchase_order_item import PurchaseOrderItem
from services.audit_service import AuditService
from interfaces.ipart_service import IPartService
from dtos.purchase_order_dto import PurchaseOrderDTO
from dtos.purchase_order_item_dto import PurchaseOrderItemDTO


class PurchaseOrderService(IPurchaseOrderService):
    """Service class for Purchase Order operations."""
    
    def __init__(self, audit_service: AuditService, part_service: IPartService = None):
        """Initialize PurchaseOrderService."""
        self.repository = PurchaseOrderRepository()
        self.item_repository = PurchaseOrderItemRepository()
        self.audit_service = audit_service
        self.part_service = part_service
        
    def create_purchase_order(self, po_data: dict, items: List[dict] = None, current_user=None, ip_address=None) -> PurchaseOrderDTO:
        """Create a new purchase order."""
        if 'branch_id' not in po_data or po_data['branch_id'] is None:
            po_data['branch_id'] = 1
        
        po = self.repository.create(po_data)
        
        if items:
            for item_data in items:
                item_data['purchase_order'] = po.id
                self.item_repository.create(item_data)
            self._update_po_total(po.id)
            # Re-fetch to get updated total/items
            po = self.repository.get(po.id)
            
        dto = PurchaseOrderDTO.from_model(po)
        
        self.audit_service.log_action(
            user=current_user,
            action="po_create",
            table_name="purchase_orders",
            new_data=dto.to_audit_dict(),
            ip_address=ip_address
        )
        return dto
        
    def get_purchase_order(self, po_id: int) -> Optional[PurchaseOrderDTO]:
        """Get a purchase order by ID."""
        po = self.repository.get(po_id)
        return PurchaseOrderDTO.from_model(po) if po else None
        
    def update_purchase_order(self, po_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[PurchaseOrderDTO]:
        """Update an existing purchase order."""
        old_po = self.repository.get(po_id)
        if not old_po:
            return None
            
        old_dto = PurchaseOrderDTO.from_model(old_po)
        po = self.repository.update(po_id, update_data)
        
        if po:
            new_dto = PurchaseOrderDTO.from_model(po)
            self.audit_service.log_action(
                user=current_user,
                action="po_update",
                table_name="purchase_orders",
                old_data=old_dto.to_audit_dict(),
                new_data=new_dto.to_audit_dict(),
                ip_address=ip_address
            )
            return new_dto
        return None
        
    def delete_purchase_order(self, po_id: int, current_user=None, ip_address=None) -> bool:
        """Delete a purchase order."""
        po = self.repository.get(po_id)
        if not po:
            return False
            
        dto = PurchaseOrderDTO.from_model(po)
        success = self.repository.delete(po_id)
        
        if success:
            self.audit_service.log_action(
                user=current_user,
                action="po_delete",
                table_name="purchase_orders",
                old_data=dto.to_audit_dict(),
                ip_address=ip_address
            )
        return success
        
    def list_purchase_orders(self, status: Optional[str] = None, branch_id: Optional[int] = None) -> List[PurchaseOrderDTO]:
        """List purchase orders with optional filtering."""
        pos = self.repository.list_all(status, branch_id)
        return [PurchaseOrderDTO.from_model(po) for po in pos]
        
    def search_purchase_orders(self, search_term: str) -> List[PurchaseOrderDTO]:
        """Search purchase orders."""
        pos = self.repository.search(search_term)
        return [PurchaseOrderDTO.from_model(po) for po in pos]
        
    def update_status(self, po_id: int, new_status: str, current_user=None, ip_address=None) -> Optional[PurchaseOrderDTO]:
        """Update PO status and trigger workflows."""
        po = self.repository.get(po_id)
        if not po:
            return None
            
        old_status = po.status
        update_data = {'status': new_status}
        
        if new_status == 'sent' and old_status != 'sent':
            self._create_invoice_for_po(po_id, current_user)
        
        if new_status == 'received' and old_status != 'received':
            update_data['received_date'] = datetime.now()
            self._process_receipt(po_id, current_user)
        elif new_status == 'cancelled':
            update_data['received_date'] = None
            self._cancel_invoice_for_po(po_id, current_user)
            
        updated_po = self.repository.update(po_id, update_data)
        
        if updated_po:
            self.audit_service.log_action(
                user=current_user,
                action="po_status_change",
                table_name="purchase_orders",
                old_data={'status': old_status},
                new_data={'status': new_status},
                ip_address=ip_address
            )
            return PurchaseOrderDTO.from_model(updated_po)
        return None

    def add_item(self, po_id: int, item_data: dict) -> Optional[PurchaseOrderItemDTO]:
        """Add a line item."""
        item_data['purchase_order'] = po_id
        item = self.item_repository.create(item_data)
        self._update_po_total(po_id)
        return PurchaseOrderItemDTO.from_model(item) if item else None

    def remove_item(self, item_id: int) -> bool:
        """Remove a line item."""
        item = self.item_repository.get(item_id)
        if item:
            po_id = item.purchase_order.id
            success = self.item_repository.delete(item_id)
            if success:
                self._update_po_total(po_id)
            return success
        return False

    def update_item(self, item_id: int, update_data: dict) -> Optional[PurchaseOrderItemDTO]:
        """Update a line item."""
        item = self.item_repository.update(item_id, update_data)
        if item:
            self._update_po_total(item.purchase_order.id)
            return PurchaseOrderItemDTO.from_model(item)
        return None

    def get_items(self, po_id: int) -> List[PurchaseOrderItemDTO]:
        """Get items for PO."""
        items = self.item_repository.get_by_po(po_id)
        return [PurchaseOrderItemDTO.from_model(item) for item in items]
    
    def _process_receipt(self, po_id: int, user=None):
        """Handle internal inventory logic (same as before)."""
        if not self.part_service:
            return
        items = self.item_repository.get_by_po(po_id)
        for item in items:
            self.part_service.update_stock(
                item.part.id, 
                item.quantity,
                reference_type='purchase_order',
                reference_id=po_id,
                notes=f"PO Receipt {item.purchase_order.po_number}",
                user=user
            )
            current_price = float(item.part.cost_price)
            po_unit_cost = float(item.unit_cost)
            if current_price != po_unit_cost:
                self.part_service.update_part(
                    item.part.id,
                    user=user,
                    cost=po_unit_cost,
                    price_change_reason=f"Updated from PO receipt (PO #{item.purchase_order.po_number})"
                )
            self.item_repository.update(item.id, {'received_quantity': item.quantity})
            
    def _create_invoice_for_po(self, po_id: int, current_user=None):
        """Internal helper to create supplier invoice."""
        from models.supplier_invoice import SupplierInvoice
        po = self.repository.get(po_id)
        if not po: return
        existing = list(SupplierInvoice.select().where(SupplierInvoice.purchase_order == po_id))
        if existing: return
        invoice_number = f"INV-{po.po_number}"
        invoice_data = {
            'purchase_order': po_id,
            'invoice_number': invoice_number,
            'invoice_date': datetime.now(),
            'subtotal': po.total_amount,
            'discount': 0.00,
            'shipping_fee': 0.00,
            'created_by': current_user
        }
        SupplierInvoice.create(**invoice_data)

    def _cancel_invoice_for_po(self, po_id: int, current_user=None):
        """Internal helper to cancel invoice."""
        from models.supplier_invoice import SupplierInvoice
        from config.constants import InvoiceStatus
        invoices = list(SupplierInvoice.select().where(SupplierInvoice.purchase_order == po_id))
        for invoice in invoices:
            if invoice.status not in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]:
                invoice.status = InvoiceStatus.CANCELLED
                invoice.save()
                if self.audit_service:
                    self.audit_service.log_action(
                        user=current_user,
                        action="update",
                        table_name="supplier_invoices",
                        old_data={"invoice_id": invoice.id},
                        new_data={"status": InvoiceStatus.CANCELLED},
                        ip_address=None
                    )

    def get_supplier_balance_info(self, supplier_id: int) -> dict:
        """Calculate supplier balance statistics."""
        from decimal import Decimal
        balance_info = {
            'total_orders': 0,
            'total_owed': Decimal('0.00'),
            'total_paid': Decimal('0.00'),
            'balance': Decimal('0.00')
        }
        
        # This uses direct model access for efficiency or repo method
        # Ideally repo should handle aggregation
        orders = self.repository.list_for_supplier(supplier_id)
        balance_info['total_orders'] = len(orders)
        
        for order in orders:
            # Logic mirroring ModernSupplierListTab
            # Status: pending/approved -> owed
            # Status: received -> paid (Wait, received means we have goods, do we owe? Usually yes until PAID)
            # ModernSupplierListTab logic was:
            # if pending/approved: owed += total
            # elif received: paid += total (This implies received means paid? That's weird business logic)
            # Usually 'received' means inventory update, but payment is separate (SupplierPayment).
            # But adhering to existing logic:
            
            amt = Decimal(str(order.total_amount or 0))
            if order.status in ['pending', 'approved']:
                balance_info['total_owed'] += amt
            elif order.status == 'received':
                # Check if it has a SupplierInvoice that is paid?
                # The view logic simply added to 'total_paid'.
                # I will preserve view logic for now to avoid regression.
                balance_info['total_paid'] += amt
                
        balance_info['balance'] = balance_info['total_owed'] - balance_info['total_paid']
        return balance_info

    def _update_po_total(self, po_id: int):
        """Internal helper (same as before)."""
        items = self.item_repository.get_by_po(po_id)
        total = sum(item.total_cost for item in items)
        self.repository.update(po_id, {'total_amount': total})