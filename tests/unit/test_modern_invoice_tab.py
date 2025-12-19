"""
Unit tests for ModernInvoiceTab using explicit dependency injection.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication
import sys
from datetime import datetime

# Ensure QApplication exists
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for testing Qt widgets"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

@pytest.fixture
def mock_invoice_dto():
    """Create a mock invoice DTO"""
    invoice = Mock()
    invoice.id = 1
    invoice.invoice_number = "INV-2023-001"
    invoice.created_at = datetime.now()
    invoice.due_date = datetime.now()
    invoice.payment_status = "unpaid"
    invoice.total = 100.0
    invoice.payments = []
    invoice.items = []
    invoice.device = Mock()
    invoice.device.brand = "Test Brand"
    invoice.device.model = "Test Model"
    invoice.device.customer = Mock()
    invoice.device.customer.name = "Test Customer"
    invoice.error_description = "Test Issue"
    return invoice

@pytest.fixture
def mock_services(mock_invoice_dto):
    """Create all mock services needed for ModernInvoiceTab"""
    services = {
        'invoice_controller': Mock(),
        'ticket_controller': Mock(),
        'business_settings_service': Mock(),
        'part_service': Mock(),
    }
    
    # Setup default return values
    services['invoice_controller'].list_invoices = Mock(return_value=[mock_invoice_dto])
    services['part_service'].get_part_by_id = Mock(return_value=None)
    
    return services

@pytest.fixture
def mock_user():
    """Mock user object"""
    user = Mock()
    user.id = 1
    user.username = "testuser"
    return user

class TestModernInvoiceTabInitialization:
    """Test ModernInvoiceTab initialization with explicit DI"""
    
    def test_init_with_explicit_dependencies(
        self,
        qapp,
        mock_services,
        mock_user
    ):
        """Test that invoice tab initializes with explicit dependencies"""
        from views.invoice.modern_invoice_tab import ModernInvoiceTab
        
        # Create tab with explicit dependencies
        tab = ModernInvoiceTab(
            invoice_controller=mock_services['invoice_controller'],
            ticket_controller=mock_services['ticket_controller'],
            business_settings_service=mock_services['business_settings_service'],
            part_service=mock_services['part_service'],
            user=mock_user,
            container=None
        )
        
        # Verify dependencies are stored
        assert tab.invoice_controller == mock_services['invoice_controller']
        assert tab.ticket_controller == mock_services['ticket_controller']
        assert tab.business_settings_service == mock_services['business_settings_service']
        assert tab.part_service == mock_services['part_service']
        assert tab.container is None

    def test_works_without_container(
        self,
        qapp,
        mock_services,
        mock_user
    ):
        """Test that invoice tab works without container"""
        from views.invoice.modern_invoice_tab import ModernInvoiceTab
        
        tab = ModernInvoiceTab(
            invoice_controller=mock_services['invoice_controller'],
            ticket_controller=mock_services['ticket_controller'],
            business_settings_service=mock_services['business_settings_service'],
            part_service=mock_services['part_service'],
            user=mock_user,
            container=None
        )
        
        assert tab.container is None
        # Should verify that methods using dependencies work
        # For example, _load_invoices calls invoice_controller
        tab._load_invoices()
        mock_services['invoice_controller'].list_invoices.assert_called()

class TestModernInvoiceTabFilters:
    """Test filtering functionality"""
    
    def test_search_filter(
        self,
        qapp,
        mock_services,
        mock_user,
        mock_invoice_dto
    ):
        """Test search filter"""
        from views.invoice.modern_invoice_tab import ModernInvoiceTab
        
        tab = ModernInvoiceTab(
            invoice_controller=mock_services['invoice_controller'],
            ticket_controller=mock_services['ticket_controller'],
            business_settings_service=mock_services['business_settings_service'],
            part_service=mock_services['part_service'],
            user=mock_user,
            container=None
        )
        
        # Test matching search
        tab.search_input.setText("INV-2023")
        
        # Ensure sub-properties are iterable/strings if filtered
        mock_invoice_dto.items = []
        mock_invoice_dto.payments = []
        
        # KEY FIX: Ensure customer_name is a string, not a Mock
        # The view uses invoice.customer_name
        mock_invoice_dto.customer_name = "Test Customer"
        
        filtered = tab._apply_filters([mock_invoice_dto])
        # assert len(filtered) == 1  <-- This might fail if the search logic doesn't match
        
        # The search logic checks:
        # 1. invoice_number
        # 2. customer_name
        
        # INV-2023 matches invoice_number "INV-2023-001"
        assert len(filtered) == 1
        
        # Test non-matching search
        tab.search_input.setText("NONEXISTENT")
        filtered = tab._apply_filters([mock_invoice_dto])
        assert len(filtered) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
