"""
Financial Service - Business logic for financial operations.
"""

from typing import List, Dict, Optional
from datetime import datetime, date
from repositories.financial_repository import FinancialRepository
from models.transaction import Transaction
from models.expense_category import ExpenseCategory
from dtos.transaction_dto import TransactionDTO
from dtos.expense_category_dto import ExpenseCategoryDTO
from services.audit_service import AuditService

class FinancialService:
    def __init__(self, repository: FinancialRepository, audit_service: AuditService):
        self.repository = repository
        self.audit_service = audit_service
        
    def add_transaction(self, 
                       amount: float, 
                       type: str, 
                       category_id: int, 
                       date_obj: datetime,
                       description: str = None,
                       payment_method: str = 'cash',
                       branch_id: int = None,
                       user_id: int = None,
                       current_user=None,
                       ip_address=None) -> TransactionDTO:
        """Add a new financial transaction."""
        
        data = {
            "amount": amount,
            "type": type,
            "category": category_id,
            "date": date_obj,
            "description": description,
            "payment_method": payment_method,
            "branch": branch_id or (getattr(current_user, 'branch_id', 1) if current_user else 1),
            "created_by": user_id or (getattr(current_user, 'id', None) if current_user else None)
        }
        
        transaction = self.repository.create_transaction(data)
        dto = TransactionDTO.from_model(transaction)
        
        self.audit_service.log_action(
            user=current_user,
            action="financial_transaction_create",
            table_name="transactions",
            new_data=dto.to_audit_dict(),
            ip_address=ip_address
        )
        
        return dto
        
    def get_dashboard_summary(self, start_date: date, end_date: date, branch_id: int = None) -> Dict:
        """Get summary stats for financial dashboard."""
        return self.repository.get_financial_summary(start_date, end_date, branch_id)
        
    def get_recent_transactions(self, limit: int = 50, branch_id: int = None) -> List[TransactionDTO]:
        """Get list of recent transactions."""
        transactions = self.repository.list_transactions(branch_id=branch_id, limit=limit)
        return [TransactionDTO.from_model(t) for t in transactions]
        
    def get_categories(self, is_income: bool = None) -> List[ExpenseCategoryDTO]:
        """Get available categories."""
        categories = self.repository.get_categories(is_income)
        return [ExpenseCategoryDTO.from_model(c) for c in categories]
        
    def add_category(self, name, is_income, color="#3B82F6", description=None, current_user=None, ip_address=None) -> ExpenseCategoryDTO:
        """Create a new category"""
        data = {
            "name": name,
            "is_income": is_income,
            "color": color,
            "description": description,
            "is_active": True
        }
        category = self.repository.create_category(data)
        dto = ExpenseCategoryDTO.from_model(category)
        
        self.audit_service.log_action(
            user=current_user,
            action="financial_category_create",
            table_name="expense_categories",
            new_data=dto.to_audit_dict(),
            ip_address=ip_address
        )
        
        return dto
        
    def update_category(self, category_id, name, is_income, color, description=None, current_user=None, ip_address=None) -> bool:
        """Update category"""
        old_category = self.repository.get_category(category_id)
        if not old_category:
            return False
            
        old_dto = ExpenseCategoryDTO.from_model(old_category)
        
        data = {
            "name": name,
            "is_income": is_income,
            "color": color,
            "description": description
        }
        success = self.repository.update_category(category_id, data)
        
        if success:
            new_category = self.repository.get_category(category_id)
            new_dto = ExpenseCategoryDTO.from_model(new_category)
            self.audit_service.log_action(
                user=current_user,
                action="financial_category_update",
                table_name="expense_categories",
                old_data=old_dto.to_audit_dict(),
                new_data=new_dto.to_audit_dict(),
                ip_address=ip_address
            )
            
        return success
        
    def delete_category(self, category_id, current_user=None, ip_address=None) -> bool:
        """Delete category (soft)"""
        category = self.repository.get_category(category_id)
        if not category:
            return False
            
        dto = ExpenseCategoryDTO.from_model(category)
        success = self.repository.delete_category(category_id)
        
        if success:
            self.audit_service.log_action(
                user=current_user,
                action="financial_category_delete",
                table_name="expense_categories",
                old_data=dto.to_audit_dict(),
                ip_address=ip_address
            )
            
        return success
        
    def delete_transaction(self, transaction_id: int, current_user=None, ip_address=None) -> bool:
        """Delete a transaction."""
        transaction = self.repository.get_transaction(transaction_id)
        if not transaction:
            return False
            
        dto = TransactionDTO.from_model(transaction)
        success = self.repository.delete_transaction(transaction_id)
        
        if success:
            self.audit_service.log_action(
                user=current_user,
                action="financial_transaction_delete",
                table_name="transactions",
                old_data=dto.to_audit_dict(),
                ip_address=ip_address
            )
            
        return success
        
    def update_transaction(self, transaction_id: int, amount, type, category_id, date_obj, description, payment_method, current_user=None, ip_address=None) -> bool:
        """Update a transaction"""
        old_transaction = self.repository.get_transaction(transaction_id)
        if not old_transaction:
            return False
            
        old_dto = TransactionDTO.from_model(old_transaction)
        
        data = {
            "amount": amount,
            "type": type,
            "category": category_id,
            "date": date_obj,
            "description": description,
            "payment_method": payment_method
        }
        success = self.repository.update_transaction(transaction_id, data)
        
        if success:
            new_transaction = self.repository.get_transaction(transaction_id)
            new_dto = TransactionDTO.from_model(new_transaction)
            self.audit_service.log_action(
                user=current_user,
                action="financial_transaction_update",
                table_name="transactions",
                old_data=old_dto.to_audit_dict(),
                new_data=new_dto.to_audit_dict(),
                ip_address=ip_address
            )
            
        return success

    def get_transaction(self, transaction_id: int) -> Optional[TransactionDTO]:
        """Get transaction by ID"""
        transaction = self.repository.get_transaction(transaction_id)
        return TransactionDTO.from_model(transaction) if transaction else None
        
    def get_expense_breakdown(self, start_date, end_date, branch_id=None) -> List[Dict]:
        """Get expense breakdown data."""
        return self.repository.get_expense_breakdown(start_date, end_date, branch_id)

    def get_income_breakdown(self, start_date, end_date, branch_id=None) -> List[Dict]:
        """Get income breakdown data."""
        return self.repository.get_income_breakdown(start_date, end_date, branch_id)
        
    def export_to_csv(self, start_date, end_date, filename: str, branch_id=None) -> bool:
        """Export transactions to CSV."""
        import csv
        try:
            transactions = self.repository.list_transactions(start_date, end_date, branch_id, limit=999999)
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Header
                writer.writerow(['Date', 'Type', 'Category', 'Description', 'Amount', 'Payment Method'])
                
                for t in transactions:
                    cat_name = t.category.name if t.category else "-"
                    writer.writerow([
                        t.date.strftime('%Y-%m-%d'),
                        t.type,
                        cat_name,
                        t.description or "",
                        f"{t.amount:.2f}",
                        t.payment_method or ""
                    ])
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False
