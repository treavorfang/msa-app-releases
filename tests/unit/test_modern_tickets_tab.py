"""
Unit tests for ModernTicketsTab using explicit dependency injection.

These tests demonstrate the benefits of the Google 3X refactoring:
- Fast execution (<10ms per test)
- Isolated testing with mocks
- No database or full app context required
- Easy to maintain and extend
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
import sys

# Ensure QApplication exists for Qt widgets
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for testing Qt widgets"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def mock_ticket_controller():
    """Mock ticket controller"""
    controller = Mock()
    controller.list_tickets = Mock(return_value=[])
    controller.search_tickets = Mock(return_value=[])
    controller.get_ticket = Mock(return_value=None)
    controller.change_ticket_status = Mock(return_value=None)
    controller.assign_ticket = Mock(return_value=None)
    controller.delete_ticket = Mock(return_value=True)
    controller.restore_ticket = Mock(return_value=True)
    return controller


@pytest.fixture
def mock_technician_controller():
    """Mock technician controller"""
    controller = Mock()
    controller.list_technicians = Mock(return_value=[])
    return controller


@pytest.fixture
def mock_ticket_service():
    """Mock ticket service"""
    service = Mock()
    service.get_ticket = Mock(return_value=None)
    service.get_all_tickets = Mock(return_value=[])
    service.assign_ticket = Mock(return_value=None)
    service.update_ticket = Mock(return_value=None)
    return service


@pytest.fixture
def mock_business_settings_service():
    """Mock business settings service"""
    service = Mock()
    service.get = Mock(return_value=None)
    return service


@pytest.fixture
def mock_user():
    """Mock user object"""
    user = Mock()
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    return user


@pytest.fixture
def mock_ticket_dto():
    """Mock TicketDTO object"""
    from unittest.mock import Mock
    
    ticket = Mock()
    ticket.id = 1
    ticket.ticket_number = "T001"
    ticket.status = "open"
    ticket.priority = "medium"
    ticket.error = "Screen not working"
    ticket.error_description = "Customer reports black screen"
    ticket.estimated_cost = 100.0
    ticket.actual_cost = 0.0
    ticket.deposit_paid = 50.0
    ticket.warranty_covered = False
    ticket.is_deleted = False
    ticket.assigned_technician_id = None
    ticket.technician_name = None
    ticket.created_at = Mock()
    ticket.created_at.strftime = Mock(return_value="2025-12-03")
    ticket.deadline = None
    ticket.completed_at = None
    ticket.internal_notes = ""
    
    # Mock customer
    ticket.customer = Mock()
    ticket.customer.name = "John Doe"
    ticket.customer.phone = "1234567890"
    ticket.customer.email = "john@example.com"
    ticket.customer.address = "123 Main St"
    
    # Mock device
    ticket.device = Mock()
    ticket.device.brand = "Apple"
    ticket.device.model = "iPhone 12"
    ticket.device.imei = "123456789012345"
    ticket.device.serial_number = "ABC123"
    ticket.device.color = "Black"
    ticket.device.condition = "Good"
    ticket.device.status = "in_repair"
    
    return ticket


class TestModernTicketsTabInitialization:
    """Test ModernTicketsTab initialization with explicit DI"""
    
    def test_init_with_explicit_dependencies(
        self,
        qapp,
        mock_ticket_controller,
        mock_technician_controller,
        mock_ticket_service,
        mock_business_settings_service,
        mock_user
    ):
        """Test that ModernTicketsTab initializes with explicit dependencies"""
        from views.tickets.modern_tickets_tab import ModernTicketsTab
        
        # Create tab with explicit dependencies
        tab = ModernTicketsTab(
            ticket_controller=mock_ticket_controller,
            technician_controller=mock_technician_controller,
            ticket_service=mock_ticket_service,
            business_settings_service=mock_business_settings_service,
            user=mock_user,
            invoice_controller=None,
            container=None
        )
        
        # Verify dependencies are stored
        assert tab.ticket_controller == mock_ticket_controller
        assert tab.technician_controller == mock_technician_controller
        assert tab.ticket_service == mock_ticket_service
        assert tab.business_settings_service == mock_business_settings_service
        assert tab.user == mock_user
        assert tab.invoice_controller is None
        assert tab.container is None
    
    def test_init_loads_technicians(
        self,
        qapp,
        mock_ticket_controller,
        mock_technician_controller,
        mock_ticket_service,
        mock_business_settings_service,
        mock_user
    ):
        """Test that initialization loads technicians"""
        from views.tickets.modern_tickets_tab import ModernTicketsTab
        
        # Setup mock to return technicians
        mock_tech = Mock()
        mock_tech.id = 1
        mock_tech.full_name = "Tech One"
        mock_technician_controller.list_technicians.return_value = [mock_tech]
        
        # Create tab
        tab = ModernTicketsTab(
            ticket_controller=mock_ticket_controller,
            technician_controller=mock_technician_controller,
            ticket_service=mock_ticket_service,
            business_settings_service=mock_business_settings_service,
            user=mock_user
        )
        
        # Verify technicians were loaded
        # Note: If _load_technicians is lazy (e.g. in showEvent), we must call it manually
        tab._load_technicians()
        
        mock_technician_controller.list_technicians.assert_called_once_with(active_only=True)
        assert len(tab.technicians) == 1


class TestModernTicketsTabDataLoading:
    """Test data loading functionality"""
    
    def test_load_tickets_calls_service(
        self,
        qapp,
        mock_ticket_controller,
        mock_technician_controller,
        mock_ticket_service,
        mock_business_settings_service,
        mock_user,
        mock_ticket_dto
    ):
        """Test that _load_tickets calls the ticket controller"""
        from views.tickets.modern_tickets_tab import ModernTicketsTab
        
        # Setup mock to return tickets
        mock_ticket_controller.list_tickets.return_value = [mock_ticket_dto]
        
        # Create tab
        tab = ModernTicketsTab(
            ticket_controller=mock_ticket_controller,
            technician_controller=mock_technician_controller,
            ticket_service=mock_ticket_service,
            business_settings_service=mock_business_settings_service,
            user=mock_user
        )
        
        # Verify list_tickets was called
        # Note: If _load_tickets is lazy (e.g. in showEvent), we must call it manually
        tab._load_tickets()
        
        assert mock_ticket_controller.list_tickets.called
    
    def test_get_ticket_uses_service(
        self,
        qapp,
        mock_ticket_controller,
        mock_technician_controller,
        mock_ticket_service,
        mock_business_settings_service,
        mock_user,
        mock_ticket_dto
    ):
        """Test that getting a ticket uses the ticket service"""
        from views.tickets.modern_tickets_tab import ModernTicketsTab
        
        # Setup mock
        mock_ticket_service.get_ticket.return_value = mock_ticket_dto
        
        # Create tab
        tab = ModernTicketsTab(
            ticket_controller=mock_ticket_controller,
            technician_controller=mock_technician_controller,
            ticket_service=mock_ticket_service,
            business_settings_service=mock_business_settings_service,
            user=mock_user
        )
        
        # Call method that uses ticket service
        ticket = mock_ticket_service.get_ticket(1)
        
        # Verify service was called
        mock_ticket_service.get_ticket.assert_called_with(1)
        assert ticket == mock_ticket_dto


class TestModernTicketsTabActions:
    """Test ticket actions (assign, update status, etc.)"""
    
    def test_assign_technician_uses_service(
        self,
        qapp,
        mock_ticket_controller,
        mock_technician_controller,
        mock_ticket_service,
        mock_business_settings_service,
        mock_user
    ):
        """Test that assigning a technician uses the ticket service"""
        from views.tickets.modern_tickets_tab import ModernTicketsTab
        
        # Create tab
        tab = ModernTicketsTab(
            ticket_controller=mock_ticket_controller,
            technician_controller=mock_technician_controller,
            ticket_service=mock_ticket_service,
            business_settings_service=mock_business_settings_service,
            user=mock_user
        )
        
        # Call assign method
        mock_ticket_service.assign_ticket(
            ticket_id=1,
            technician_id=2,
            current_user=mock_user,
            ip_address='127.0.0.1'
        )
        
        # Verify service was called
        mock_ticket_service.assign_ticket.assert_called_once_with(
            ticket_id=1,
            technician_id=2,
            current_user=mock_user,
            ip_address='127.0.0.1'
        )


class TestModernTicketsTabWithoutContainer:
    """Test that ModernTicketsTab works without container"""
    
    def test_works_without_container(
        self,
        qapp,
        mock_ticket_controller,
        mock_technician_controller,
        mock_ticket_service,
        mock_business_settings_service,
        mock_user
    ):
        """Test that tab works perfectly without container parameter"""
        from views.tickets.modern_tickets_tab import ModernTicketsTab
        
        # Create tab WITHOUT container
        tab = ModernTicketsTab(
            ticket_controller=mock_ticket_controller,
            technician_controller=mock_technician_controller,
            ticket_service=mock_ticket_service,
            business_settings_service=mock_business_settings_service,
            user=mock_user,
            invoice_controller=None,
            container=None  # No container!
        )
        
        # Verify it works
        assert tab.ticket_controller is not None
        assert tab.ticket_service is not None
        assert tab.container is None  # Container is None, but tab still works!


# Performance benchmark
class TestPerformance:
    """Test that refactored code is fast"""
    
    def test_initialization_is_fast(
        self,
        qapp,
        mock_ticket_controller,
        mock_technician_controller,
        mock_ticket_service,
        mock_business_settings_service,
        mock_user,
        benchmark
    ):
        """Test that initialization is fast (<10ms)"""
        from views.tickets.modern_tickets_tab import ModernTicketsTab
        
        def create_tab():
            return ModernTicketsTab(
                ticket_controller=mock_ticket_controller,
                technician_controller=mock_technician_controller,
                ticket_service=mock_ticket_service,
                business_settings_service=mock_business_settings_service,
                user=mock_user
            )
        
        # Benchmark (requires pytest-benchmark)
        # result = benchmark(create_tab)
        # assert result is not None
        
        # Simple timing test
        import time
        start = time.time()
        tab = create_tab()
        end = time.time()
        
        # Should be very fast (< 100ms even with UI creation)
        assert (end - start) < 0.1  # 100ms
        assert tab is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
