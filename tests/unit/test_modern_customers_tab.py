"""
Unit tests for ModernCustomersTab using explicit dependency injection.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication
import sys
from datetime import datetime
from decimal import Decimal

# Ensure QApplication exists
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for testing Qt widgets"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

@pytest.fixture
def mock_customer_dto():
    """Create a mock customer DTO"""
    customer = Mock()
    customer.id = 1
    customer.name = "Test Customer"
    customer.phone = "1234567890"
    customer.email = "test@example.com"
    customer.address = "123 Test St"
    customer.updated_at = datetime.now()
    return customer

@pytest.fixture
def mock_services(mock_customer_dto):
    """Create all mock services needed for ModernCustomersTab"""
    services = {
        'customer_controller': Mock(),
        'invoice_controller': Mock(),
    }
    
    # Setup default return values
    services['customer_controller'].get_all_customers = Mock(return_value=[mock_customer_dto])
    services['customer_controller'].get_all_customers_including_deleted = Mock(return_value=[mock_customer_dto])
    services['customer_controller'].get_customer_devices = Mock(return_value=[])
    services['customer_controller'].data_changed = Mock()
    services['customer_controller'].data_changed.connect = Mock()
    
    services['invoice_controller'].invoice_created = Mock()
    services['invoice_controller'].invoice_created.connect = Mock()
    services['invoice_controller'].invoice_updated = Mock()
    services['invoice_controller'].invoice_updated.connect = Mock()
    
    return services

@pytest.fixture
def mock_user():
    """Mock user object"""
    user = Mock()
    user.id = 1
    user.username = "testuser"
    return user

class TestModernCustomersTabInitialization:
    """Test ModernCustomersTab initialization with explicit DI"""
    
    def test_init_with_explicit_dependencies(
        self,
        qapp,
        mock_services,
        mock_user
    ):
        """Test that customers tab initializes with explicit dependencies"""
        from views.customer.modern_customers_tab import ModernCustomersTab
        
        # Create tab with explicit dependencies
        tab = ModernCustomersTab(
            customer_controller=mock_services['customer_controller'],
            invoice_controller=mock_services['invoice_controller'],
            user=mock_user,
            container=None
        )
        
        # Verify dependencies are stored
        assert tab.customer_controller == mock_services['customer_controller']
        assert tab.invoice_controller == mock_services['invoice_controller']
        assert tab.user == mock_user
        assert tab.container is None

    def test_works_without_container(
        self,
        qapp,
        mock_services,
        mock_user
    ):
        """Test that customers tab works without container"""
        from views.customer.modern_customers_tab import ModernCustomersTab
        
        tab = ModernCustomersTab(
            customer_controller=mock_services['customer_controller'],
            invoice_controller=mock_services['invoice_controller'],
            user=mock_user,
            container=None
        )
        
        assert tab.container is None
        # Should verify that methods using dependencies work
        # For example, _load_customers calls customer_controller
        tab._load_customers()
        mock_services['customer_controller'].get_all_customers.assert_called()

class TestModernCustomersTabFilters:
    """Test filtering functionality"""
    
    def test_search_filter(
        self,
        qapp,
        mock_services,
        mock_user,
        mock_customer_dto
    ):
        """Test search filter"""
        from views.customer.modern_customers_tab import ModernCustomersTab
        
        tab = ModernCustomersTab(
            customer_controller=mock_services['customer_controller'],
            invoice_controller=mock_services['invoice_controller'],
            user=mock_user,
            container=None
        )
        
        # Test matching search
        tab.search_input.setText("Test Customer")
        tab._load_customers()
        
        # Verify customer controller was called
        mock_services['customer_controller'].get_all_customers.assert_called()

class TestModernCustomersTabBalanceCalculation:
    """Test balance calculation"""
    
    def test_calculate_customer_balance(
        self,
        qapp,
        mock_services,
        mock_user,
        mock_customer_dto
    ):
        """Test customer balance calculation"""
        from views.customer.modern_customers_tab import ModernCustomersTab
        
        tab = ModernCustomersTab(
            customer_controller=mock_services['customer_controller'],
            invoice_controller=mock_services['invoice_controller'],
            user=mock_user,
            container=None
        )
        
        # Mock controller methods instead of raw models
        # ModernCustomersTab._calculate_customer_balance calls customer_controller.get_customer_debt_status
        # or performs calculations using controller data.
        
        # NOTE: If logic is inside the tab, we mock the query results.
        # But if logic is in controller, we mock the controller.
        
        # Let's inspect what _calculate_customer_balance actually does.
        # Assuming it calls:
        # invoices = self.invoice_controller.get_customer_invoices(customer_id)
        # return { ... }
        
        # MOCK the expected calls on the controllers
        # The method calls get_customer_balance_info, NOT get_customer_invoices
        mock_services['invoice_controller'].get_customer_balance_info = Mock(return_value={
            'total_invoices': 5,
            'total_owed': Decimal('100.00'),
            'total_credit': Decimal('0.00'),
            'balance': Decimal('100.00')
        })
        
        # Now call the method
        balance_info = tab._calculate_customer_balance(mock_customer_dto.id)
        
        # Verify structure
        assert 'total_invoices' in balance_info
        assert 'total_owed' in balance_info
        assert 'total_credit' in balance_info
        assert 'balance' in balance_info

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
