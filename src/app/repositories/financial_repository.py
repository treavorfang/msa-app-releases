"""
Financial Repository - Data access for transactions.
"""

from typing import List, Optional, Dict
from datetime import datetime
from peewee import fn
from models.transaction import Transaction
from models.expense_category import ExpenseCategory
from models.invoice import Invoice
from config.database import db

class FinancialRepository:
    """Repository for financial data access."""
    
    # --- Categories ---
    
    def create_category(self, data: dict) -> ExpenseCategory:
        return ExpenseCategory.create(**data)
        
    def get_categories(self, is_income: Optional[bool] = None) -> List[ExpenseCategory]:
        query = ExpenseCategory.select().where(ExpenseCategory.is_active == True)
        if is_income is not None:
            query = query.where(ExpenseCategory.is_income == is_income)
        return list(query)
        
    def update_category(self, category_id: int, data: dict) -> bool:
        """Update a category"""
        try:
            query = ExpenseCategory.update(**data).where(ExpenseCategory.id == category_id)
            query.execute()
            return True
        except:
            return False

    def delete_category(self, category_id: int) -> bool:
        """Soft delete a category"""
        try:
            query = ExpenseCategory.update(is_active=False).where(ExpenseCategory.id == category_id)
            query.execute()
            return True
        except:
            return False
    
    # --- Transactions ---
    
    def create_transaction(self, data: dict) -> Transaction:
        return Transaction.create(**data)
        
    def list_transactions(self, start_date=None, end_date=None, branch_id=None, limit=50) -> List[Transaction]:
        query = Transaction.select().order_by(Transaction.date.desc())
        
        if start_date:
            query = query.where(fn.DATE(Transaction.date) >= start_date)
        if end_date:
            query = query.where(fn.DATE(Transaction.date) <= end_date)
            
        if branch_id:
            query = query.where(Transaction.branch == branch_id)
            
        return list(query.limit(limit))

    def delete_transaction(self, transaction_id: int) -> bool:
        try:
            Transaction.delete_by_id(transaction_id)
            return True
        except:
            return False

    def update_transaction(self, transaction_id: int, data: dict) -> bool:
        """Update an existing transaction"""
        try:
            query = Transaction.update(**data).where(Transaction.id == transaction_id)
            query.execute()
            return True
        except Exception as e:
            print(f"Error updating transaction: {e}")
            return False

    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID"""
        try:
            return Transaction.get_by_id(transaction_id)
        except:
            return None

    # --- Aggregation ---
    
    def get_manual_income(self, start_date, end_date, branch_id=None) -> float:
        """Sum of manual 'income' transactions."""
        query = (Transaction
            .select(fn.SUM(Transaction.amount))
            .where(
                (Transaction.type == 'income') &
                (fn.DATE(Transaction.date) >= start_date) &
                (fn.DATE(Transaction.date) <= end_date)
            )
        )
        if branch_id:
            query = query.where(Transaction.branch == branch_id)
        return float(query.scalar() or 0.0)

    def get_manual_expense(self, start_date, end_date, branch_id=None) -> float:
        """Sum of manual 'expense' transactions."""
        query = (Transaction
            .select(fn.SUM(Transaction.amount))
            .where(
                (Transaction.type == 'expense') &
                (fn.DATE(Transaction.date) >= start_date) &
                (fn.DATE(Transaction.date) <= end_date)
            )
        )
        if branch_id:
            query = query.where(Transaction.branch == branch_id)
        return float(query.scalar() or 0.0)
        
    def get_invoice_revenue(self, start_date, end_date, branch_id=None) -> float:
        """Get revenue from Invoices (automatic income)."""
        # start_date/end_date might be date objects, convert to datetime for compatibility if needed
        # Assuming Invoice.created_at comparison works with dates automatically in Peewee or needs casting
        
        query = Invoice.select(fn.SUM(Invoice.total)).where(
            (fn.DATE(Invoice.created_at) >= start_date) &
            (fn.DATE(Invoice.created_at) <= end_date)
        )
        if branch_id:
            query = query.where(Invoice.branch == branch_id)
        return float(query.scalar() or 0.0)

    def get_financial_summary(self, start_date, end_date, branch_id=None) -> Dict:
        """Get total income (invoices + manual), total expense, and balance."""
        
        invoice_income = self.get_invoice_revenue(start_date, end_date, branch_id)
        manual_income = self.get_manual_income(start_date, end_date, branch_id)
        
        total_income = invoice_income + manual_income
        total_expense = self.get_manual_expense(start_date, end_date, branch_id)
        
        return {
            "invoice_income": invoice_income,
            "manual_income": manual_income,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_balance": total_income - total_expense
        }

    def get_expense_breakdown(self, start_date, end_date, branch_id=None) -> List[Dict]:
        """Get expense breakdown by category."""
        try:
            query = (
                Transaction
                .select(
                    ExpenseCategory.name, 
                    ExpenseCategory.color, 
                    fn.SUM(Transaction.amount).alias('total')
                )
                .join(ExpenseCategory)
                .where(
                    (Transaction.type == 'expense') &
                    (fn.DATE(Transaction.date) >= start_date) &
                    (fn.DATE(Transaction.date) <= end_date)
                )
                .group_by(ExpenseCategory.name, ExpenseCategory.color)
                .order_by(fn.SUM(Transaction.amount).desc())
            )
            
            if branch_id:
                query = query.where(Transaction.branch == branch_id)
                
            return [
                {
                    "name": item.category.name,
                    "color": item.category.color,
                    "amount": float(item.total)
                } for item in query
            ]
        except Exception as e:
            print(f"Error getting breakdown: {e}")
            return []
    def get_income_breakdown(self, start_date, end_date, branch_id=None) -> List[Dict]:
        """Get income breakdown by category (including Invoices)."""
        data = []
        try:
            # 1. Manual Income Transactions
            query = (
                Transaction
                .select(
                    ExpenseCategory.name, 
                    ExpenseCategory.color, 
                    fn.SUM(Transaction.amount).alias('total')
                )
                .join(ExpenseCategory)
                .where(
                    (Transaction.type == 'income') &
                    (fn.DATE(Transaction.date) >= start_date) &
                    (fn.DATE(Transaction.date) <= end_date)
                )
                .group_by(ExpenseCategory.name, ExpenseCategory.color)
            )
            
            if branch_id:
                query = query.where(Transaction.branch == branch_id)
                
            for item in query:
                data.append({
                    "name": item.category.name,
                    "color": item.category.color,
                    "amount": float(item.total)
                })
                
            # 2. Invoices (Sales)
            invoice_revenue = self.get_invoice_revenue(start_date, end_date, branch_id)
            if invoice_revenue > 0:
                data.append({
                    "name": "Sales (Invoices)",
                    "color": "#3B82F6", # Blue
                    "amount": invoice_revenue
                })
                
            # Sort by amount desc
            data.sort(key=lambda x: x['amount'], reverse=True)
            return data
            
        except Exception as e:
            print(f"Error getting income breakdown: {e}")
            return []
