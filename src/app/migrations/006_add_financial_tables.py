"""
Migration: Add Financial Tables
Version: 006
Description: Creates expense_categories and transactions tables, and seeds initial data.
"""

from peewee import *
from datetime import datetime

# Import models to ensure they are defined
from models.expense_category import ExpenseCategory
from models.transaction import Transaction
from models.permission import Permission
from models.role import Role
from models.role_permission import RolePermission

def apply(db):
    """Apply the migration."""
    print("Migrating: Creating Financial Tables...")
    
    # 1. Create Tables
    db.create_tables([ExpenseCategory, Transaction], safe=True)
    
    # 2. Seed Expense Categories
    default_categories = [
        {"name": "Sales", "description": "Income from sales", "is_income": True, "color": "#10B981"},
        {"name": "Service", "description": "Income from services", "is_income": True, "color": "#34D399"},
        {"name": "Rent", "description": "Office rent", "is_income": False, "color": "#EF4444"},
        {"name": "Utilities", "description": "Electricity, Water, Internet", "is_income": False, "color": "#F59E0B"},
        {"name": "Salaries", "description": "Staff salaries", "is_income": False, "color": "#3B82F6"},
        {"name": "Supplies", "description": "Office supplies", "is_income": False, "color": "#6366F1"},
        {"name": "Tax", "description": "Tax payments", "is_income": False, "color": "#8B5CF6"},
        {"name": "Marketing", "description": "Advertising and promo", "is_income": False, "color": "#EC4899"},
        {"name": "Other", "description": "Miscellaneous", "is_income": False, "color": "#6B7280"},
    ]
    
    for cat_data in default_categories:
        ExpenseCategory.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        
    print(" - Seeded Expense Categories")
    
    # 3. Seed Permissions
    permissions = [
        ('financial:view', 'View Financial', 'financial', 'View financial transactions'),
        ('financial:manage', 'Manage Financial', 'financial', 'Add/Edit transactions'),
    ]
    
    created_perms = []
    for code, name, category, desc in permissions:
        perm, _ = Permission.get_or_create(
            code=code,
            defaults={'name': name, 'category': category, 'description': desc}
        )
        created_perms.append(perm)
        
    print(" - Seeded Financial Permissions")
    
    # 4. Assign Permissions to Roles
    # Admin gets everything (usually handled by wildcard or explicit add)
    # Manager gets access
    roles_to_update = ['admin', 'manager']
    
    for role_name in roles_to_update:
        try:
            role = Role.get(Role.name == role_name)
            for perm in created_perms:
                RolePermission.get_or_create(role=role, permission=perm)
            print(f" - Assigned permissions to role: {role_name}")
        except Role.DoesNotExist:
            print(f" - Warning: Role {role_name} not found")

