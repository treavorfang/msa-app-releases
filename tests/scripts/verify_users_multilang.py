import sys
import os
from PySide6.QtWidgets import QApplication
from datetime import date

# Add src and src/app to path
sys.path.append(os.path.join(os.getcwd(), "src"))
sys.path.append(os.path.join(os.getcwd(), "src", "app"))

from app.utils.language_manager import language_manager
from app.utils.currency_formatter import currency_formatter
from app.views.technician.technicians import TechniciansTab
from app.views.technician.technician_details_dialog import TechnicianDetailsDialog
from app.views.technician.bonus_management_dialog import BonusManagementDialog
from app.views.technician.performance_dashboard_dialog import PerformanceDashboardDialog
from app.views.auth.login import LoginView
from app.views.auth.register import RegisterView
from app.models.technician import Technician
from unittest.mock import MagicMock

def verify_users_multilang():
    # Create QApplication if it doesn't exist
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    print("Initializing Managers...")
    # Ensure managers are initialized (they are singletons)
    lm = language_manager
    cf = currency_formatter
    
    print("Managers initialized.")

    # Mock container and user
    mock_container = MagicMock()
    mock_user = MagicMock()
    mock_user.id = 1

    # Mock Technician
    mock_tech = Technician(
        id=1,
        username="tech1",
        email="tech1@example.com",
        full_name="John Doe",
        role="Technician",
        status="Active",
        hourly_rate=50.0,
        commission_rate=10.0,
        color="#3498db",
        initials="JD",
        phone="123-456-7890",
        address="123 Tech St",
        joined_date=date.today()
    )

    print("Verifying TechniciansTab...")
    try:
        # TechniciansTab requires container and user
        tab = TechniciansTab(mock_container, mock_user)
        print("TechniciansTab instantiated successfully.")
    except Exception as e:
        print(f"FAILED to instantiate TechniciansTab: {e}")
        import traceback
        traceback.print_exc()

    print("Verifying TechnicianDetailsDialog...")
    try:
        dialog = TechnicianDetailsDialog(mock_container, mock_tech)
        print("TechnicianDetailsDialog instantiated successfully.")
    except Exception as e:
        print(f"FAILED to instantiate TechnicianDetailsDialog: {e}")
        import traceback
        traceback.print_exc()

    print("Verifying BonusManagementDialog...")
    try:
        dialog = BonusManagementDialog(mock_container, mock_tech)
        print("BonusManagementDialog instantiated successfully.")
    except Exception as e:
        print(f"FAILED to instantiate BonusManagementDialog: {e}")
        import traceback
        traceback.print_exc()

    print("Verifying PerformanceDashboardDialog...")
    try:
        dialog = PerformanceDashboardDialog(mock_container, mock_tech)
        print("PerformanceDashboardDialog instantiated successfully.")
    except Exception as e:
        print(f"FAILED to instantiate PerformanceDashboardDialog: {e}")
        import traceback
        traceback.print_exc()

    print("Verifying LoginView...")
    try:
        view = LoginView()
        print("LoginView instantiated successfully.")
    except Exception as e:
        print(f"FAILED to instantiate LoginView: {e}")
        import traceback
        traceback.print_exc()

    print("Verifying RegisterView...")
    try:
        view = RegisterView()
        print("RegisterView instantiated successfully.")
    except Exception as e:
        print(f"FAILED to instantiate RegisterView: {e}")
        import traceback
        traceback.print_exc()

    print("Verification Complete.")


if __name__ == "__main__":
    verify_users_multilang()
