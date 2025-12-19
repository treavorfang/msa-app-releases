"""
Unit tests for ModernDashboardTab

Tests the modern dashboard tab with mocked dependencies to ensure:
- Proper initialization with explicit DI
- Data loading and refresh functionality
- EventBus event handling
- UI component creation
- Quick actions functionality
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timedelta
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDate
import sys
import os

# Add src/app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'app'))

# Ensure QApplication exists for widget tests
if not QApplication.instance():
    app = QApplication(sys.argv)

from views.modern_dashboard import ModernDashboardTab
from core.event_bus import EventBus
from core.events import (
    TicketCreatedEvent, TicketUpdatedEvent, InvoiceCreatedEvent,
    CustomerCreatedEvent
)


def setup_device_mock(mock_device_class):
    """Helper to properly configure Device model mock"""
    # Mock Device.select() to return empty query
    mock_query = Mock()
    mock_count_query = Mock()
    mock_count_query.count.return_value = 0
    mock_query.where.return_value = mock_count_query
    mock_device_class.select.return_value = mock_query
    
    # Mock Device attributes for comparison operations
    # These need to support comparison operators (>=, <=, !=, ==) and & operator
    # Create a mock that supports & operator
    def create_chainable_mock():
        m = Mock()
        # Use a lambda to avoid infinite recursion during definition
        m.__and__ = Mock(side_effect=lambda *args: create_chainable_mock())
        return m
    
    mock_status = Mock()
    mock_status.__ne__ = Mock(return_value=create_chainable_mock())
    mock_device_class.status = mock_status
    
    mock_received_at = Mock()
    mock_received_at.__ge__ = Mock(return_value=create_chainable_mock())
    mock_received_at.__le__ = Mock(return_value=create_chainable_mock())
    mock_device_class.received_at = mock_received_at
    
    mock_is_deleted = Mock()
    mock_is_deleted.__eq__ = Mock(return_value=create_chainable_mock())
    mock_device_class.is_deleted = mock_is_deleted
    
    return mock_device_class



class TestModernDashboardTabInitialization:
    """Test dashboard initialization with explicit dependency injection"""
    
    def _create_mock_ticket_service(self):
        """Helper to create properly mocked ticket service"""
        mock_service = Mock()
        mock_service.get_ticket_statistics.return_value = {
            'total': 10,
            'open': 5,
            'in_progress': 2,
            'completed': 3
        }
        mock_service.get_dashboard_stats_range.return_value = {
            'total_tickets': 10,
            'new_jobs': 5,
            'in_progress': 2,
            'completed': 3,
            'cancelled': 0,
            'revenue': 1000.0,
            'completion_rate': 75
        }
        mock_service.get_recent_tickets.return_value = []
        mock_service.get_average_completion_time.return_value = 24.5
        mock_service.get_revenue_trend.return_value = []
        mock_service.get_technician_performance.return_value = []
        return mock_service
    
    @patch('models.device.Device')
    def test_init_with_all_dependencies(self, mock_device_class):
        """Test dashboard initializes correctly with all dependencies"""
        setup_device_mock(mock_device_class)
        
        # Arrange
        mock_ticket_service = self._create_mock_ticket_service()
        mock_ticket_controller = Mock()
        mock_customer_controller = Mock()
        mock_technician_controller = Mock()
        mock_repair_part_controller = Mock()
        mock_work_log_controller = Mock()
        mock_business_settings_service = Mock()
        mock_part_service = Mock()
        mock_technician_repository = Mock()
        mock_technician_repository.get_all_technicians.return_value = []
        mock_user = Mock()
        mock_user.id = 1
        
        # Act
        dashboard = ModernDashboardTab(
            ticket_service=mock_ticket_service,
            ticket_controller=mock_ticket_controller,
            customer_controller=mock_customer_controller,
            technician_controller=mock_technician_controller,
            repair_part_controller=mock_repair_part_controller,
            work_log_controller=mock_work_log_controller,
            business_settings_service=mock_business_settings_service,
            part_service=mock_part_service,
            technician_repository=mock_technician_repository,
            user=mock_user
        )
        
        # Assert
        assert dashboard.ticket_service == mock_ticket_service
        assert dashboard.ticket_controller == mock_ticket_controller
        assert dashboard.customer_controller == mock_customer_controller
        assert dashboard.user == mock_user
        assert dashboard.container is None  # No container needed
    
    @patch('models.device.Device')
    def test_init_with_container_for_legacy_support(self, mock_device):
        """Test dashboard can still accept container for legacy support"""
        setup_device_mock(mock_device)
        
        # Arrange
        mock_container = Mock()
        mock_user = Mock()
        mock_ticket_service = self._create_mock_ticket_service()
        mock_technician_repository = Mock()
        mock_technician_repository.get_all_technicians.return_value = []
        
        # Act
        dashboard = ModernDashboardTab(
            ticket_service=mock_ticket_service,
            ticket_controller=Mock(),
            customer_controller=Mock(),
            technician_controller=Mock(),
            repair_part_controller=Mock(),
            work_log_controller=Mock(),
            business_settings_service=Mock(),
            part_service=Mock(),
            technician_repository=mock_technician_repository,
            user=mock_user,
            container=mock_container
        )
        
        # Assert
        assert dashboard.container == mock_container
    
    @patch('models.device.Device')
    def test_ui_components_created(self, mock_device):
        """Test that key UI components are created during initialization"""
        setup_device_mock(mock_device)
        
        # Arrange & Act
        mock_ticket_service = self._create_mock_ticket_service()
        mock_technician_repository = Mock()
        mock_technician_repository.get_all_technicians.return_value = []
        
        dashboard = ModernDashboardTab(
            ticket_service=mock_ticket_service,
            ticket_controller=Mock(),
            customer_controller=Mock(),
            technician_controller=Mock(),
            repair_part_controller=Mock(),
            work_log_controller=Mock(),
            business_settings_service=Mock(),
            part_service=Mock(),
            technician_repository=mock_technician_repository,
            user=Mock()
        )
        
        # Assert - Check key UI elements exist
        assert hasattr(dashboard, 'date_range_combo')
        assert hasattr(dashboard, 'revenue_canvas')  # Was revenue_chart_container
        assert hasattr(dashboard, 'tickets_list_layout')  # Was recent_tickets_list
        assert hasattr(dashboard, 'stats_layout')  # Was quick_stats_container
        assert hasattr(dashboard, 'tech_perf_layout')  # Was tech_performance_container

class TestModernDashboardTabDataLoading:
    """Test data loading and refresh functionality"""
    
    @patch('models.device.Device')
    def test_refresh_data_calls_update_methods(self, mock_device):
        """Test refresh_data calls all update methods"""
        setup_device_mock(mock_device)
        
        # Arrange
        mock_ticket_service = Mock()
        mock_ticket_service.get_dashboard_stats_range.return_value = {
            'total_tickets': 10,
            'new_jobs': 5,
            'in_progress': 2,
            'completed': 3,
            'revenue': 1000.0,
            'completion_rate': 75
        }
        mock_ticket_service.get_average_completion_time.return_value = 24.5
        mock_ticket_service.get_recent_tickets.return_value = []
        mock_ticket_service.get_revenue_trend.return_value = []
        mock_ticket_service.get_technician_performance.return_value = []
        
        dashboard = ModernDashboardTab(
            ticket_service=mock_ticket_service,
            ticket_controller=Mock(),
            customer_controller=Mock(),
            technician_controller=Mock(),
            repair_part_controller=Mock(),
            work_log_controller=Mock(),
            business_settings_service=Mock(),
            part_service=Mock(),
            technician_repository=Mock(),
            user=Mock()
        )
        
        # Mock the update methods
        dashboard._update_metric_cards = Mock()
        dashboard._update_revenue_chart = Mock()
        dashboard._update_recent_tickets = Mock()
        dashboard._update_quick_stats = Mock()
        dashboard._update_technician_performance = Mock()
        
        # Act
        dashboard.refresh_data()
        
        # Assert
        dashboard._update_metric_cards.assert_called_once()
        dashboard._update_revenue_chart.assert_called_once()
        dashboard._update_recent_tickets.assert_called_once()
        dashboard._update_quick_stats.assert_called_once()
        dashboard._update_technician_performance.assert_called_once()
    
    @patch('models.device.Device')
    def test_update_recent_tickets_loads_tickets(self, mock_device):
        """Test _update_recent_tickets loads and displays tickets"""
        setup_device_mock(mock_device)
        
        # Arrange
        mock_ticket_service = Mock()
        mock_ticket_service.get_dashboard_stats_range.return_value = {
            'total_tickets': 10,
            'new_jobs': 5,
            'in_progress': 2,
            'completed': 3,
            'revenue': 1000.0,
            'completion_rate': 75
        }
        mock_ticket_service.get_average_completion_time.return_value = 24.5
        mock_ticket_service.get_recent_tickets.return_value = []
        mock_ticket_service.get_revenue_trend.return_value = []
        mock_ticket_service.get_technician_performance.return_value = []
        t1 = Mock(id=1, ticket_number='T-001', status='open', device=Mock(brand='Apple', model='iPhone'), error='Screen broken', created_at=datetime.now())
        t1.customer = Mock()
        t1.customer.name = 'John'
        
        t2 = Mock(id=2, ticket_number='T-002', status='in_progress', device=Mock(brand='Samsung', model='Galaxy'), error='Battery issue', created_at=datetime.now())
        t2.customer = Mock()
        t2.customer.name = 'Jane'

        mock_ticket_service.get_recent_tickets.return_value = [t1, t2]
        
        dashboard = ModernDashboardTab(
            ticket_service=mock_ticket_service,
            ticket_controller=Mock(),
            customer_controller=Mock(),
            technician_controller=Mock(),
            repair_part_controller=Mock(),
            work_log_controller=Mock(),
            business_settings_service=Mock(),
            part_service=Mock(),
            technician_repository=Mock(),
            user=Mock()
        )
        
        # Act
        mock_ticket_service.reset_mock()
        dashboard._update_recent_tickets()
        
        # Assert
        mock_ticket_service.get_recent_tickets.assert_called_once()
        # Verify tickets were processed (layout should have items)
        assert dashboard.tickets_list_layout.count() > 0


class TestModernDashboardTabEventBus:
    """Test EventBus integration"""
    
    def setup_method(self):
        """Clear EventBus before each test"""
        EventBus.clear()
    
    @patch('models.device.Device')
    def test_subscribes_to_all_domain_events(self, mock_device):
        """Test dashboard subscribes to all domain events"""
        setup_device_mock(mock_device)
        
        # Arrange
        mock_ticket_service = Mock()
        mock_ticket_service.get_dashboard_stats_range.return_value = {
            'total_tickets': 10,
            'new_jobs': 5,
            'in_progress': 2,
            'completed': 3,
            'revenue': 1000.0,
            'completion_rate': 75
        }
        mock_ticket_service.get_average_completion_time.return_value = 24.5
        mock_ticket_service.get_recent_tickets.return_value = []
        mock_ticket_service.get_revenue_trend.return_value = []
        mock_ticket_service.get_technician_performance.return_value = []
        mock_ticket_service.get_recent_tickets.return_value = []
        mock_ticket_service.get_revenue_trend.return_value = []
        mock_ticket_service.get_technician_performance.return_value = []
        mock_ticket_service.get_recent_tickets.return_value = []
        mock_ticket_service.get_revenue_trend.return_value = []
        mock_ticket_service.get_technician_performance.return_value = []
        
        dashboard = ModernDashboardTab(
            ticket_service=mock_ticket_service,
            ticket_controller=Mock(),
            customer_controller=Mock(),
            technician_controller=Mock(),
            repair_part_controller=Mock(),
            work_log_controller=Mock(),
            business_settings_service=Mock(),
            part_service=Mock(),
            technician_repository=Mock(),
            user=Mock()
        )
        
        # Act - Subscribe to events
        dashboard._subscribe_to_events()
        
        # Assert - Check subscriptions exist
        assert len(EventBus._subscribers[TicketCreatedEvent]) > 0
        assert len(EventBus._subscribers[InvoiceCreatedEvent]) > 0
        assert len(EventBus._subscribers[CustomerCreatedEvent]) > 0
    
    @patch('models.device.Device')
    @patch('PySide6.QtCore.QTimer')
    def test_handles_ticket_created_event(self, mock_qtimer, mock_device):
        """Test dashboard refreshes when ticket created event is published"""
        setup_device_mock(mock_device)
        
        # Arrange
        mock_ticket_service = Mock()
        mock_ticket_service.get_dashboard_stats_range.return_value = {
            'total_tickets': 10,
            'new_jobs': 5,
            'in_progress': 2,
            'completed': 3,
            'revenue': 1000.0,
            'completion_rate': 75
        }
        mock_ticket_service.get_average_completion_time.return_value = 24.5
        mock_ticket_service.get_recent_tickets.return_value = []
        mock_ticket_service.get_revenue_trend.return_value = []
        mock_ticket_service.get_technician_performance.return_value = []
        mock_ticket_service.get_recent_tickets.return_value = []
        mock_ticket_service.get_revenue_trend.return_value = []
        mock_ticket_service.get_technician_performance.return_value = []
        
        dashboard = ModernDashboardTab(
            ticket_service=mock_ticket_service,
            ticket_controller=Mock(),
            customer_controller=Mock(),
            technician_controller=Mock(),
            repair_part_controller=Mock(),
            work_log_controller=Mock(),
            business_settings_service=Mock(),
            part_service=Mock(),
            technician_repository=Mock(),
            user=Mock()
        )
        
        dashboard._subscribe_to_events()
        dashboard.refresh_data = Mock()
        
        # Act - Publish event
        EventBus.publish(TicketCreatedEvent(ticket_id=1, user_id=1))
        
        # Assert - QTimer.singleShot should be called to schedule refresh
        mock_qtimer.singleShot.assert_called()
    
    @patch('models.device.Device')
    def test_unsubscribes_on_close(self, mock_device):
        """Test dashboard unsubscribes from events when closed"""
        setup_device_mock(mock_device)
        
        # Arrange
        mock_ticket_service = Mock()
        mock_ticket_service.get_dashboard_stats_range.return_value = {
            'total_tickets': 10,
            'new_jobs': 5,
            'in_progress': 2,
            'completed': 3,
            'revenue': 1000.0,
            'completion_rate': 75
        }
        mock_ticket_service.get_average_completion_time.return_value = 24.5
        mock_ticket_service.get_recent_tickets.return_value = []
        mock_ticket_service.get_revenue_trend.return_value = []
        mock_ticket_service.get_technician_performance.return_value = []
        mock_ticket_service.get_recent_tickets.return_value = []
        mock_ticket_service.get_revenue_trend.return_value = []
        mock_ticket_service.get_technician_performance.return_value = []
        
        dashboard = ModernDashboardTab(
            ticket_service=mock_ticket_service,
            ticket_controller=Mock(),
            customer_controller=Mock(),
            technician_controller=Mock(),
            repair_part_controller=Mock(),
            work_log_controller=Mock(),
            business_settings_service=Mock(),
            part_service=Mock(),
            technician_repository=Mock(),
            user=Mock()
        )
        
        dashboard._subscribe_to_events()
        initial_subscriber_count = len(EventBus._subscribers[TicketCreatedEvent])
        
        # Act
        dashboard._unsubscribe_from_events()
        
        # Assert
        final_subscriber_count = len(EventBus._subscribers[TicketCreatedEvent])
        assert final_subscriber_count < initial_subscriber_count


class TestModernDashboardTabQuickActions:
    """Test quick action functionality"""
    
    @patch('models.device.Device')
    def test_new_ticket_action_calls_controller(self, mock_device):
        """Test new ticket button calls ticket controller"""
        setup_device_mock(mock_device)
        
        # Arrange
        mock_ticket_service = Mock()
        mock_ticket_service.get_dashboard_stats_range.return_value = {
            'total_tickets': 10,
            'new_jobs': 5,
            'in_progress': 2,
            'completed': 3,
            'revenue': 1000.0,
            'completion_rate': 75
        }
        mock_ticket_service.get_average_completion_time.return_value = 24.5
        mock_ticket_service.get_recent_tickets.return_value = []
        mock_ticket_service.get_revenue_trend.return_value = []
        mock_ticket_service.get_technician_performance.return_value = []
        mock_ticket_service.get_recent_tickets.return_value = []
        mock_ticket_service.get_revenue_trend.return_value = []
        mock_ticket_service.get_technician_performance.return_value = []
        
        mock_ticket_controller = Mock()
        dashboard = ModernDashboardTab(
            ticket_service=mock_ticket_service,
            ticket_controller=mock_ticket_controller,
            customer_controller=Mock(),
            technician_controller=Mock(),
            repair_part_controller=Mock(),
            work_log_controller=Mock(),
            business_settings_service=Mock(),
            part_service=Mock(),
            technician_repository=Mock(),
            user=Mock(id=1)
        )
        
        # Act
        dashboard._on_new_ticket()
        
        # Assert
        mock_ticket_controller.show_new_ticket_receipt.assert_called_once_with(
            user_id=1,
            parent=dashboard
        )
    
    @patch('models.device.Device')
    def test_new_customer_action_calls_controller(self, mock_device):
        """Test new customer button calls customer controller"""
        setup_device_mock(mock_device)
        
        # Arrange
        mock_ticket_service = Mock()
        mock_ticket_service.get_dashboard_stats_range.return_value = {
            'total_tickets': 10,
            'new_jobs': 5,
            'in_progress': 2,
            'completed': 3,
            'revenue': 1000.0,
            'completion_rate': 75
        }
        mock_ticket_service.get_average_completion_time.return_value = 24.5
        mock_ticket_service.get_recent_tickets.return_value = []
        mock_ticket_service.get_revenue_trend.return_value = []
        mock_ticket_service.get_technician_performance.return_value = []
        mock_ticket_service.get_recent_tickets.return_value = []
        mock_ticket_service.get_revenue_trend.return_value = []
        mock_ticket_service.get_technician_performance.return_value = []
        
        mock_customer_controller = Mock()
        dashboard = ModernDashboardTab(
            ticket_service=mock_ticket_service,
            ticket_controller=Mock(),
            customer_controller=mock_customer_controller,
            technician_controller=Mock(),
            repair_part_controller=Mock(),
            work_log_controller=Mock(),
            business_settings_service=Mock(),
            part_service=Mock(),
            technician_repository=Mock(),
            user=Mock(id=1)
        )
        
        # Act
        dashboard._on_new_customer()
        
        # Assert
        mock_customer_controller.show_new_customer_form.assert_called_once_with(
            user_id=1,
            parent=dashboard
        )


class TestModernDashboardTabDateRange:
    """Test date range functionality"""
    
    @patch('models.device.Device')
    def test_date_range_change_refreshes_data(self, mock_device):
        """Test changing date range triggers data refresh"""
        setup_device_mock(mock_device)
        
        # Arrange
        mock_ticket_service = Mock()
        mock_ticket_service.get_dashboard_stats_range.return_value = {
            'total_tickets': 10,
            'new_jobs': 5,
            'in_progress': 2,
            'completed': 3,
            'revenue': 1000.0,
            'completion_rate': 75
        }
        mock_ticket_service.get_average_completion_time.return_value = 24.5
        mock_ticket_service.get_recent_tickets.return_value = []
        mock_ticket_service.get_revenue_trend.return_value = []
        mock_ticket_service.get_technician_performance.return_value = []
        mock_ticket_service.get_recent_tickets.return_value = []
        mock_ticket_service.get_revenue_trend.return_value = []
        mock_ticket_service.get_technician_performance.return_value = []
        
        dashboard = ModernDashboardTab(
            ticket_service=mock_ticket_service,
            ticket_controller=Mock(),
            customer_controller=Mock(),
            technician_controller=Mock(),
            repair_part_controller=Mock(),
            work_log_controller=Mock(),
            business_settings_service=Mock(),
            part_service=Mock(),
            technician_repository=Mock(),
            user=Mock()
        )
        
        dashboard._update_revenue_chart = Mock()
        dashboard._update_technician_performance = Mock()
        
        # Act
        dashboard._on_date_range_changed(1)  # Change to "This Week"
        
        # Assert
        dashboard._update_revenue_chart.assert_called_once()
        dashboard._update_technician_performance.assert_called_once()


# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
