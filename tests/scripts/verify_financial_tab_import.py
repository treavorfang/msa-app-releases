import os, sys
from unittest.mock import MagicMock
sys.path.append(os.path.abspath('src/app'))
from core.dependency_container import DependencyContainer
from views.financial.modern_financial_tab import ModernFinancialTab
from PySide6.QtWidgets import QApplication

# Create QApplication
app = QApplication.instance() or QApplication(sys.argv)

from types import SimpleNamespace

# Create mock container
container = SimpleNamespace()
container.financial_service = MagicMock()
container.financial_service.get_dashboard_summary.return_value = {
    'total_income': 1000.0, 'total_expense': 500.0, 'net_balance': 500.0
}
container.financial_service.get_expense_breakdown.return_value = {}
container.financial_service.get_income_breakdown.return_value = {}
container.financial_service.get_recent_transactions.return_value = []

user = MagicMock()
try:
    tab = ModernFinancialTab(container)
    print('ModernFinancialTab imported and instantiated successfully')
except Exception as e:
    import traceback
    print('Error during FinancialTab import:', e)
    traceback.print_exc()
