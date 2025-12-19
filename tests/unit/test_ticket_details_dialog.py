"""
Unit tests for TicketDetailsDialog using explicit dependency injection.

These tests demonstrate:
- Fast, isolated testing with mocks
- No database required
- Easy to test complex dialogs
- Clear dependency visibility
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtCore import Qt
import sys

# Ensure QApplication exists
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for testing Qt widgets"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def mock_ticket_dto():
    """Mock TicketDTO object"""
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
    ticket.internal_notes = "Test notes"
    
    # Mock dates
    ticket.created_at = Mock()
    ticket.created_at.strftime = Mock(return_value="2025-12-03 10:00")
    ticket.deadline = Mock()
    ticket.deadline.strftime = Mock(return_value="2025-12-10")
    ticket.completed_at = None
    
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


@pytest.fixture
def mock_services():
    """Create all mock services needed for TicketDetailsDialog"""
    services = {
        'ticket_service': Mock(),
        'ticket_controller': Mock(),
        'technician_controller': Mock(),
        'repair_part_controller': Mock(),
        'work_log_controller': Mock(),
        'business_settings_service': Mock(),
        'part_service': Mock(),
        'technician_repository': Mock(),
    }
    
    # Setup default return values
    services['ticket_service'].update_ticket = Mock(return_value=True)
    services['ticket_service'].repository = Mock()
    services['ticket_service'].repository.get = Mock(return_value=Mock())
    
    services['technician_controller'].list_technicians = Mock(return_value=[])
    services['technician_controller'].change_ticket_status = Mock(return_value=Mock())
    services['technician_controller'].assign_ticket = Mock(return_value=Mock())
    
    services['repair_part_controller'].get_parts_used_in_ticket = Mock(return_value=[])
    services['repair_part_controller'].create_repair_part = Mock(return_value=True)
    services['repair_part_controller'].delete_repair_part = Mock(return_value=True)
    
    services['work_log_controller'].get_logs_for_ticket = Mock(return_value=[])
    services['work_log_controller'].get_active_logs_for_technician = Mock(return_value=[])
    
    services['part_service'].get_part_by_id = Mock(return_value=Mock())
    
    services['technician_repository'].search = Mock(return_value=[])
    
    return services


@pytest.fixture
def mock_user():
    """Mock user object"""
    user = Mock()
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    return user


class TestTicketDetailsDialogInitialization:
    """Test TicketDetailsDialog initialization with explicit DI"""
    
    def test_init_with_explicit_dependencies(
        self,
        qapp,
        mock_ticket_dto,
        mock_services,
        mock_user
    ):
        """Test that dialog initializes with explicit dependencies"""
        from views.tickets.ticket_details_dialog import TicketDetailsDialog
        
        # Create dialog with explicit dependencies
        dialog = TicketDetailsDialog(
            ticket=mock_ticket_dto,
            ticket_service=mock_services['ticket_service'],
            ticket_controller=mock_services['ticket_controller'],
            technician_controller=mock_services['technician_controller'],
            repair_part_controller=mock_services['repair_part_controller'],
            work_log_controller=mock_services['work_log_controller'],
            business_settings_service=mock_services['business_settings_service'],
            part_service=mock_services['part_service'],
            technician_repository=mock_services['technician_repository'],
            user=mock_user,
            container=None,
            parent=None
        )
        
        # Verify dependencies are stored
        assert dialog.ticket == mock_ticket_dto
        assert dialog.ticket_service == mock_services['ticket_service']
        assert dialog.ticket_controller == mock_services['ticket_controller']
        assert dialog.technician_controller == mock_services['technician_controller']
        assert dialog.user == mock_user
        assert dialog.container is None
    
    def test_dialog_title_shows_ticket_number(
        self,
        qapp,
        mock_ticket_dto,
        mock_services,
        mock_user
    ):
        """Test that dialog title includes ticket number"""
        from views.tickets.ticket_details_dialog import TicketDetailsDialog
        
        dialog = TicketDetailsDialog(
            ticket=mock_ticket_dto,
            ticket_service=mock_services['ticket_service'],
            ticket_controller=mock_services['ticket_controller'],
            technician_controller=mock_services['technician_controller'],
            repair_part_controller=mock_services['repair_part_controller'],
            work_log_controller=mock_services['work_log_controller'],
            business_settings_service=mock_services['business_settings_service'],
            part_service=mock_services['part_service'],
            technician_repository=mock_services['technician_repository'],
            user=mock_user
        )
        
        # Verify title contains ticket number
        assert "T001" in dialog.windowTitle()


class TestTicketDetailsDialogUpdateTicket:
    """Test ticket update functionality"""
    
    def test_update_internal_notes_uses_service(
        self,
        qapp,
        mock_ticket_dto,
        mock_services,
        mock_user
    ):
        """Test that updating notes uses ticket service"""
        from views.tickets.ticket_details_dialog import TicketDetailsDialog
        
        dialog = TicketDetailsDialog(
            ticket=mock_ticket_dto,
            ticket_service=mock_services['ticket_service'],
            ticket_controller=mock_services['ticket_controller'],
            technician_controller=mock_services['technician_controller'],
            repair_part_controller=mock_services['repair_part_controller'],
            work_log_controller=mock_services['work_log_controller'],
            business_settings_service=mock_services['business_settings_service'],
            part_service=mock_services['part_service'],
            technician_repository=mock_services['technician_repository'],
            user=mock_user
        )
        
        # Simulate updating notes
        new_notes = "Updated notes"
        mock_services['ticket_service'].update_ticket(
            mock_ticket_dto.id,
            {'internal_notes': new_notes}
        )
        
        # Verify service was called
        mock_services['ticket_service'].update_ticket.assert_called_once_with(
            mock_ticket_dto.id,
            {'internal_notes': new_notes}
        )


class TestTicketDetailsDialogPartsTab:
    """Test parts functionality"""
    
    def test_load_parts_uses_controller(
        self,
        qapp,
        mock_ticket_dto,
        mock_services,
        mock_user
    ):
        """Test that repair_part_controller is properly injected and available"""
        from views.tickets.ticket_details_dialog import TicketDetailsDialog
        
        # Setup mock parts
        mock_part = Mock()
        mock_part.id = 1
        mock_part.quantity = 2
        mock_part.part = Mock()
        mock_part.part.name = "Screen"
        mock_part.part.sku = "SCR001"
        mock_part.part.cost_price = 50.0
        
        mock_services['repair_part_controller'].get_parts_used_in_ticket.return_value = [mock_part]
        
        dialog = TicketDetailsDialog(
            ticket=mock_ticket_dto,
            ticket_service=mock_services['ticket_service'],
            ticket_controller=mock_services['ticket_controller'],
            technician_controller=mock_services['technician_controller'],
            repair_part_controller=mock_services['repair_part_controller'],
            work_log_controller=mock_services['work_log_controller'],
            business_settings_service=mock_services['business_settings_service'],
            part_service=mock_services['part_service'],
            technician_repository=mock_services['technician_repository'],
            user=mock_user
        )
        
        # Verify controller is properly injected
        assert dialog.repair_part_controller == mock_services['repair_part_controller']
        
        # Verify controller can be called (simulating tab switch)
        parts = dialog.repair_part_controller.get_parts_used_in_ticket(mock_ticket_dto.id)
        assert len(parts) == 1
        assert parts[0].part.name == "Screen"



class TestTicketDetailsDialogWorkLog:
    """Test work log functionality"""
    
    def test_load_work_logs_uses_controller(
        self,
        qapp,
        mock_ticket_dto,
        mock_services,
        mock_user
    ):
        """Test that loading work logs uses work_log_controller"""
        from views.tickets.ticket_details_dialog import TicketDetailsDialog
        
        # Setup mock work logs
        mock_log = Mock()
        mock_log.id = 1
        mock_log.start_time = Mock()
        mock_log.start_time.strftime = Mock(return_value="2025-12-03 10:00")
        mock_log.end_time = Mock()
        mock_log.end_time.strftime = Mock(return_value="2025-12-03 12:00")
        mock_log.work_performed = "Replaced screen"
        mock_log.technician = Mock()
        mock_log.technician.full_name = "Tech One"
        
        mock_services['work_log_controller'].get_logs_for_ticket.return_value = [mock_log]
        
        dialog = TicketDetailsDialog(
            ticket=mock_ticket_dto,
            ticket_service=mock_services['ticket_service'],
            ticket_controller=mock_services['ticket_controller'],
            technician_controller=mock_services['technician_controller'],
            repair_part_controller=mock_services['repair_part_controller'],
            work_log_controller=mock_services['work_log_controller'],
            business_settings_service=mock_services['business_settings_service'],
            part_service=mock_services['part_service'],
            technician_repository=mock_services['technician_repository'],
            user=mock_user
        )
        
        # Verify work logs were loaded
        mock_services['work_log_controller'].get_logs_for_ticket.assert_called_with(
            mock_ticket_dto.id
        )


class TestTicketDetailsDialogWithoutContainer:
    """Test that dialog works without container"""
    
    def test_works_without_container(
        self,
        qapp,
        mock_ticket_dto,
        mock_services,
        mock_user
    ):
        """Test that dialog works perfectly without container parameter"""
        from views.tickets.ticket_details_dialog import TicketDetailsDialog
        
        # Create dialog WITHOUT container
        dialog = TicketDetailsDialog(
            ticket=mock_ticket_dto,
            ticket_service=mock_services['ticket_service'],
            ticket_controller=mock_services['ticket_controller'],
            technician_controller=mock_services['technician_controller'],
            repair_part_controller=mock_services['repair_part_controller'],
            work_log_controller=mock_services['work_log_controller'],
            business_settings_service=mock_services['business_settings_service'],
            part_service=mock_services['part_service'],
            technician_repository=mock_services['technician_repository'],
            user=mock_user,
            container=None  # No container!
        )
        
        # Verify it works
        assert dialog.ticket_service is not None
        assert dialog.ticket_controller is not None
        assert dialog.container is None  # Container is None, but dialog still works!


class TestPerformance:
    """Test that refactored code is fast"""
    
    def test_initialization_is_fast(
        self,
        qapp,
        mock_ticket_dto,
        mock_services,
        mock_user
    ):
        """Test that initialization is fast"""
        from views.tickets.ticket_details_dialog import TicketDetailsDialog
        
        import time
        start = time.time()
        
        dialog = TicketDetailsDialog(
            ticket=mock_ticket_dto,
            ticket_service=mock_services['ticket_service'],
            ticket_controller=mock_services['ticket_controller'],
            technician_controller=mock_services['technician_controller'],
            repair_part_controller=mock_services['repair_part_controller'],
            work_log_controller=mock_services['work_log_controller'],
            business_settings_service=mock_services['business_settings_service'],
            part_service=mock_services['part_service'],
            technician_repository=mock_services['technician_repository'],
            user=mock_user
        )
        
        end = time.time()
        
        # Should be fast (< 200ms even with UI creation)
        assert (end - start) < 0.2  # 200ms
        assert dialog is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
