"""
Expense Category Model - Financial classification.
"""

from peewee import AutoField, CharField, BooleanField, TextField
from models.base_model import BaseModel

class ExpenseCategory(BaseModel):
    """
    Model for categorizing financial transactions (income/expense).
    """
    
    id = AutoField()
    
    name = CharField(
        max_length=50,
        unique=True,
        help_text="Category name (e.g., Rent, Sales, Salary)"
    )
    
    description = TextField(
        null=True,
        help_text="Optional description"
    )
    
    is_income = BooleanField(
        default=False,
        help_text="True for income categories, False for expense"
    )
    
    color = CharField(
        max_length=20,
        default="#3B82F6",
        help_text="Color code for UI visualization"
    )
    
    is_active = BooleanField(
        default=True,
        help_text="Whether category is active"
    )
    
    class Meta:
        table_name = 'expense_categories'
    
    def __str__(self):
        return self.name
