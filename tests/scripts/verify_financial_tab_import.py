import os, sys
sys.path.append(os.path.abspath('src'))
from app.core.dependency_container import DependencyContainer
from app.views.financial.financial_tab import FinancialTab

container = DependencyContainer()
user = None
try:
    tab = FinancialTab(container, user)
    print('FinancialTab imported and instantiated successfully')
except Exception as e:
    import traceback
    print('Error during FinancialTab import:', e)
    traceback.print_exc()
