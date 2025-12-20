"""TransactionDTO - Data Transfer Object for Financial Transactions."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

@dataclass
class TransactionDTO:
    """Data Transfer Object for Transaction."""
    id: Optional[int] = None
    date: Optional[datetime] = None
    amount: float = 0.0
    type: str = ""
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    description: Optional[str] = None
    payment_method: str = "cash"
    reference_id: Optional[str] = None
    branch_id: Optional[int] = None
    created_by_id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_model(cls, transaction) -> 'TransactionDTO':
        """Convert Transaction model to DTO."""
        return cls(
            id=transaction.id,
            date=transaction.date,
            amount=float(transaction.amount) if transaction.amount else 0.0,
            type=transaction.type,
            category_id=transaction.category.id if transaction.category else None,
            category_name=transaction.category.name if transaction.category else None,
            description=transaction.description,
            payment_method=transaction.payment_method,
            reference_id=transaction.reference_id,
            branch_id=transaction.branch.id if transaction.branch else None,
            created_by_id=transaction.created_by.id if transaction.created_by else None,
            created_at=transaction.created_at
        )
    
    def to_audit_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            'transaction_id': self.id,
            'date': self.date.isoformat() if hasattr(self.date, 'isoformat') else self.date,
            'amount': self.amount,
            'type': self.type,
            'category_id': self.category_id,
            'category_name': self.category_name,
            'description': self.description,
            'payment_method': self.payment_method,
            'reference_id': self.reference_id,
            'branch_id': self.branch_id,
            'created_by_id': self.created_by_id,
            'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else self.created_at
        }
