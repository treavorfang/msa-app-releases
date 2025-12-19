"""CreditNoteService - Credit Note Management Logic.

This service manages supplier credit notes using DTOs.
"""

from typing import List, Optional, Any, Dict
from decimal import Decimal
from datetime import datetime
from interfaces.icredit_note_service import ICreditNoteService
from models.credit_note import CreditNote
from repositories.credit_note_repository import CreditNoteRepository
from services.audit_service import AuditService
from dtos.credit_note_dto import CreditNoteDTO


class CreditNoteService(ICreditNoteService):
    """Service class for Credit Note operations."""
    
    def __init__(self, audit_service: Optional[AuditService] = None):
        """Initialize CreditNoteService."""
        self.repository = CreditNoteRepository()
        self.audit_service = audit_service
    
    def create_credit_note(self, credit_data: dict, current_user=None, ip_address=None) -> CreditNoteDTO:
        """Create a new credit note with auto-generated number."""
        # Generate credit note number if not provided
        if 'credit_note_number' not in credit_data:
            credit_count = CreditNote.select().count()
            credit_note_number = f"CN-{datetime.now().strftime('%Y%m%d')}-{credit_count + 1:04d}"
            credit_data['credit_note_number'] = credit_note_number
            
        credit_data['remaining_credit'] = credit_data.get('credit_amount', 0)
        
        credit_note = self.repository.create(credit_data)
        dto = CreditNoteDTO.from_model(credit_note)
        
        if self.audit_service:
            self.audit_service.log_action(
                user=current_user,
                action="credit_note_create",
                table_name="credit_notes",
                new_data=dto.to_audit_dict(),
                ip_address=ip_address
            )
        return dto
    
    def get_credit_note(self, cn_id: int) -> Optional[CreditNoteDTO]:
        """Get a credit note by ID."""
        cn = self.repository.get(cn_id)
        return CreditNoteDTO.from_model(cn) if cn else None
        
    def update_credit_note(self, cn_id: int, update_data: dict, current_user=None, ip_address=None) -> Optional[CreditNoteDTO]:
        """Update a credit note."""
        old_cn = self.repository.get(cn_id)
        if not old_cn:
            return None
            
        old_dto = CreditNoteDTO.from_model(old_cn)
        credit_note = self.repository.update(cn_id, update_data)
        
        if credit_note:
            new_dto = CreditNoteDTO.from_model(credit_note)
            if self.audit_service:
                self.audit_service.log_action(
                    user=current_user,
                    action="credit_note_update",
                    table_name="credit_notes",
                    old_data=old_dto.to_audit_dict(),
                    new_data=new_dto.to_audit_dict(),
                    ip_address=ip_address
                )
            return new_dto
        return None
        
    def delete_credit_note(self, cn_id: int, current_user=None, ip_address=None) -> bool:
        """Delete a credit note."""
        cn = self.repository.get(cn_id)
        if not cn:
            return False
            
        dto = CreditNoteDTO.from_model(cn)
        success = self.repository.delete(cn_id)
        
        if success and self.audit_service:
            self.audit_service.log_action(
                user=current_user,
                action="credit_note_delete",
                table_name="credit_notes",
                old_data=dto.to_audit_dict(),
                ip_address=ip_address
            )
        return success
    
    def generate_from_return(self, return_id: int, current_user=None, ip_address=None) -> Optional[CreditNoteDTO]:
        """Generate a credit note from an approved purchase return."""
        from models.purchase_return import PurchaseReturn
        
        purchase_return = PurchaseReturn.get_by_id(return_id)
        if not purchase_return or purchase_return.status != 'approved':
            return None
        
        # Check if credit note already exists
        existing = self.repository.get_by_return(return_id)
        if existing:
            return CreditNoteDTO.from_model(existing[0])
        
        credit_data = {
            'purchase_return': return_id,
            'credit_amount': purchase_return.total_amount,
            'issue_date': datetime.now(),
            'expiry_date': None,
            'notes': f"Credit for return {purchase_return.return_number}"
        }
        
        return self.create_credit_note(credit_data, current_user, ip_address)
    
    def apply_credit_to_invoice(self, cn_id: int, invoice_id: int, amount: Decimal, current_user=None, ip_address=None) -> bool:
        """Apply credit to a supplier invoice."""
        credit_note = self.repository.get(cn_id)
        if not credit_note or float(credit_note.remaining_credit) < float(amount):
            return False
        
        # Update credit note
        new_applied = float(credit_note.applied_amount) + float(amount)
        self.repository.update(cn_id, {
            'applied_amount': new_applied,
            'supplier_invoice': invoice_id
        })
        
        # Update invoice
        from models.supplier_invoice import SupplierInvoice
        invoice = SupplierInvoice.get_by_id(invoice_id)
        if invoice:
            new_paid = float(invoice.paid_amount) + float(amount)
            # Use raw query or repo if possible, but model save works here
            invoice.paid_amount = new_paid
            invoice.save()
        
        if self.audit_service:
            self.audit_service.log_action(
                user=current_user,
                action="credit_apply",
                table_name="credit_notes",
                old_data={'credit_note_id': cn_id},
                new_data={'invoice_id': invoice_id, 'amount': float(amount)},
                ip_address=ip_address
            )
        
        return True
    
    def get_available_credits(self, supplier_id: int) -> List[CreditNoteDTO]:
        """Get all available credits for a supplier."""
        cns = self.repository.get_available_credits(supplier_id)
        return [CreditNoteDTO.from_model(cn) for cn in cns]
    
    def list_credit_notes(self, status: Optional[str] = None) -> List[CreditNoteDTO]:
        """List all credit notes."""
        if status:
            cns = self.repository.get_by_status(status)
        else:
            cns = self.repository.get_all()
        return [CreditNoteDTO.from_model(cn) for cn in cns]

    def get_expiring_credits(self, days: int = 30) -> List[CreditNoteDTO]:
        """Get credits expiring soon."""
        # Assuming repository might not support this directly yet, or use generic filter
        # Keeping it minimal or implementing if repo has it.
        # Original service didn't have it explicitly but Interface now requires it.
        # I'll implement via list_all + filter for now.
        all_cns = self.repository.get_all()
        expiring = []
        now = datetime.now()
        for cn in all_cns:
            if cn.expiry_date:
                delta = cn.expiry_date - now
                if 0 < delta.days <= days and cn.remaining_credit > 0:
                    expiring.append(cn)
        return [CreditNoteDTO.from_model(cn) for cn in expiring]
