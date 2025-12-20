"""
Transaction Model - Financial records.
"""

from datetime import datetime
from peewee import AutoField, CharField, DecimalField, DateTimeField, ForeignKeyField, TextField
from models.base_model import BaseModel
from models.expense_category import ExpenseCategory
from models.branch import Branch
from models.user import User

class Transaction(BaseModel):
    """
    Model for manual financial transactions (Income/Expense).
    """
    
    id = AutoField()
    
    date = DateTimeField(
        default=datetime.now,
        help_text="Date of transaction"
    )
    
    amount = DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Transaction amount"
    )
    
    type = CharField(
        max_length=10,
        choices=['income', 'expense'],
        help_text="Type: income or expense"
    )
    
    category = ForeignKeyField(
        ExpenseCategory,
        backref='transactions',
        on_delete='RESTRICT',
        help_text="Category of the transaction"
    )
    
    description = TextField(
        null=True,
        help_text="Details about the transaction"
    )
    
    payment_method = CharField(
        max_length=20,
        default='cash',
        help_text="Payment method (cash, card, bank, etc.)"
    )
    
    reference_id = CharField(
        max_length=50,
        null=True,
        help_text="External reference (e.g. receipt #)"
    )
    
    branch = ForeignKeyField(
        Branch,
        backref='transactions',
        null=True,
        on_delete='SET NULL'
    )
    
    created_by = ForeignKeyField(
        User,
        backref='transactions_created',
        null=True,
        on_delete='SET NULL'
    )
    
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'transactions'
    
    def __str__(self):
        return f"{self.type.title()} - {self.amount}"
