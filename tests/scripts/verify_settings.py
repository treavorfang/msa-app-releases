
import sys
import os
from PySide6.QtWidgets import QApplication

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'app')))

from unittest.mock import MagicMock

try:
    from views.setting.settings import SettingsTab
    
    app = QApplication(sys.argv)
    
    # Mock dependencies
    container = MagicMock()
    container.settings_service.get_user_settings.return_value = {}
    container.theme_controller.available_themes = {}
    container.theme_controller.current_theme = "light"
    container.role_service.user_has_role.return_value = False
    
    # Mock business settings
    mock_business_settings = MagicMock()
    mock_business_settings.business_name = "Test Business"
    mock_business_settings.business_phone = "1234567890"
    mock_business_settings.address = "123 Test St"
    mock_business_settings.tax_id = "12345"
    mock_business_settings.notes = "Test Notes"
    mock_business_settings.default_tax_rate = 0.0
    mock_business_settings.logo_url = None
    container.business_settings_service.get_settings.return_value = mock_business_settings
    
    user = MagicMock()
    user.id = 1
    
    # Instantiate SettingsTab
    settings_tab = SettingsTab(container, user)
    print("SUCCESS: SettingsTab instantiated successfully.")
    
except AttributeError as e:
    print(f"FAILURE: AttributeError: {e}")
except Exception as e:
    print(f"FAILURE: Other Error ({type(e).__name__}): {e}")

