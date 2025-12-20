from config.database import db
from models.transaction import Transaction
from models.expense_category import ExpenseCategory
from repositories.financial_repository import FinancialRepository
from datetime import datetime, timedelta

def debug_financials():
    db.init("database/msa_dev.db")
    print("--- Transactions ---")
    transactions = Transaction.select()
    for t in transactions:
        cat_name = t.category.name if t.category else "None"
        print(f"ID: {t.id} | Date: {t.date} | Type: '{t.type}' | Amount: {t.amount} | Cat: {cat_name} | Branch: {t.branch}")

    repo = FinancialRepository()
    today = datetime.now().date()
    start = today.replace(day=1) # Month start
    end = today
    
    print(f"\n--- Range: {start} to {end} ---")
    
    print("\n--- Expense Breakdown Query Result (Global) ---")
    try:
        breakdown = repo.get_expense_breakdown(start, end, branch_id=None)
        for item in breakdown:
            print(item)
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Income Breakdown Query Result (Global) ---")
    try:
        breakdown = repo.get_income_breakdown(start, end, branch_id=None)
        for item in breakdown:
            print(item)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_financials()
