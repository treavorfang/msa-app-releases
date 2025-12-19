import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget
import sys
from datetime import datetime

from core.events import (
    TicketCreatedEvent, TicketUpdatedEvent, TicketDeletedEvent,
    InvoiceCreatedEvent, InvoiceUpdatedEvent, InvoiceDeletedEvent,
    CustomerCreatedEvent
)
from core.event_bus import EventBus

# Ensure QApplication exists
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

@pytest.fixture
def mock_user():
    user = Mock()
    user.id = 1
    user.username = "testuser"
    return user

@pytest.fixture
def mock_ticket_controller():
    controller = Mock()
    controller.list_tickets = Mock(return_value=[])
    controller.ticket_created = Mock()
    controller.ticket_updated = Mock()
    controller.ticket_deleted = Mock()
    controller.ticket_restored = Mock()
    controller.status_changed = Mock()
    controller.technician_assigned = Mock()
    return controller

@pytest.fixture
def mock_technician_controller():
    controller = Mock()
    controller.list_technicians = Mock(return_value=[])
    controller.technician_created = Mock()
    controller.technician_updated = Mock()
    return controller

@pytest.fixture
def mock_invoice_controller():
    controller = Mock()
    controller.list_invoices = Mock(return_value=[])
    controller.invoice_created = Mock()
    controller.invoice_updated = Mock()
    return controller

@pytest.fixture
def mock_customer_controller():
    controller = Mock()
    controller.get_recent_customers = Mock(return_value=[])
    return controller

@pytest.fixture
def mock_ticket_service():
    service = Mock()
    service.get_all_tickets = Mock(return_value=[])
    service.get_dashboard_stats_range = Mock(return_value={
        'total_tickets': 10,
        'revenue': 1000,
        'completion_rate': 80
    })
    return service

@pytest.fixture
def mock_business_settings_service():
    service = Mock()
    service.get = Mock(return_value=None)
    return service

@pytest.fixture
def mock_part_service():
    service = Mock()
    return service

class TestEventBusMigration:
    
    def test_modern_tickets_tab_subscription(
        self, qapp, mock_ticket_controller, mock_technician_controller,
        mock_ticket_service, mock_business_settings_service, mock_user, mock_invoice_controller
    ):
        from views.tickets.modern_tickets_tab import ModernTicketsTab
        
        with patch('core.event_bus.EventBus.subscribe') as mock_subscribe:
            tab = ModernTicketsTab(
                ticket_controller=mock_ticket_controller,
                technician_controller=mock_technician_controller,
                ticket_service=mock_ticket_service,
                business_settings_service=mock_business_settings_service,
                user=mock_user,
                invoice_controller=mock_invoice_controller
            )
            
            # Verify subscriptions
            subscribed_events = [args[0] for args, _ in mock_subscribe.call_args_list]
            assert TicketCreatedEvent in subscribed_events
            assert TicketUpdatedEvent in subscribed_events
            assert InvoiceCreatedEvent in subscribed_events

    def test_modern_tickets_tab_event_handling(
        self, qapp, mock_ticket_controller, mock_technician_controller,
        mock_ticket_service, mock_business_settings_service, mock_user
    ):
        from views.tickets.modern_tickets_tab import ModernTicketsTab
        
        tab = ModernTicketsTab(
            ticket_controller=mock_ticket_controller,
            technician_controller=mock_technician_controller,
            ticket_service=mock_ticket_service,
            business_settings_service=mock_business_settings_service,
            user=mock_user
        )
        
        # Mock _on_ticket_changed
        tab._on_ticket_changed = Mock()
        
        # Simulate event
        with patch('PySide6.QtCore.QTimer.singleShot') as mock_timer:
            event = TicketCreatedEvent(ticket_id=1, user_id=1)
            tab._handle_ticket_event(event)
            
            # Verify timer called to trigger reload
            mock_timer.assert_called_once()
            # Verify it calls _load_tickets
            callback = mock_timer.call_args[0][1]
            assert callback == tab._load_tickets

    def test_modern_invoice_tab_subscription(
        self, qapp, mock_invoice_controller, mock_ticket_controller,
        mock_business_settings_service, mock_part_service, mock_user
    ):
        from views.invoice.modern_invoice_tab import ModernInvoiceTab
        
        with patch('core.event_bus.EventBus.subscribe') as mock_subscribe:
            tab = ModernInvoiceTab(
                invoice_controller=mock_invoice_controller,
                ticket_controller=mock_ticket_controller,
                business_settings_service=mock_business_settings_service,
                part_service=mock_part_service,
                user=mock_user
            )
            
            # Verify subscriptions
            subscribed_events = [args[0] for args, _ in mock_subscribe.call_args_list]
            assert InvoiceCreatedEvent in subscribed_events
            assert InvoiceUpdatedEvent in subscribed_events
            assert InvoiceDeletedEvent in subscribed_events

    def test_modern_invoice_tab_event_handling(
        self, qapp, mock_invoice_controller, mock_ticket_controller,
        mock_business_settings_service, mock_part_service, mock_user
    ):
        from views.invoice.modern_invoice_tab import ModernInvoiceTab
        
        tab = ModernInvoiceTab(
            invoice_controller=mock_invoice_controller,
            ticket_controller=mock_ticket_controller,
            business_settings_service=mock_business_settings_service,
            part_service=mock_part_service,
            user=mock_user
        )
        
        # Mock _load_invoices
        tab._load_invoices = Mock()
        
        # Simulate event
        with patch('PySide6.QtCore.QTimer.singleShot') as mock_timer:
            event = InvoiceCreatedEvent(invoice_id=1, user_id=1)
            tab._handle_invoice_event(event)
            
            # Verify timer called
            mock_timer.assert_called_once()
            callback = mock_timer.call_args[0][1]
            assert callback == tab._load_invoices

    def test_modern_dashboard_tab_subscription(
        self, qapp, mock_ticket_service, mock_ticket_controller, mock_customer_controller,
        mock_technician_controller, mock_business_settings_service, mock_part_service, mock_user
    ):
        from views.modern_dashboard import ModernDashboardTab
        
        # Mock missing dependencies
        mock_repair_part_controller = Mock()
        mock_work_log_controller = Mock()
        mock_technician_repository = Mock()
        
        with patch('core.event_bus.EventBus.subscribe') as mock_subscribe, \
             patch.object(ModernDashboardTab, 'refresh_data'):
            
            tab = ModernDashboardTab(
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
            
            # Verify subscriptions
            subscribed_events = [args[0] for args, _ in mock_subscribe.call_args_list]
            assert TicketCreatedEvent in subscribed_events
            assert InvoiceCreatedEvent in subscribed_events
            assert CustomerCreatedEvent in subscribed_events

    def test_modern_dashboard_tab_event_handling(
        self, qapp, mock_ticket_service, mock_ticket_controller, mock_customer_controller,
        mock_technician_controller, mock_business_settings_service, mock_part_service, mock_user
    ):
        from views.modern_dashboard import ModernDashboardTab
        
        # Mock missing dependencies
        mock_repair_part_controller = Mock()
        mock_work_log_controller = Mock()
        mock_technician_repository = Mock()
        
        with patch.object(ModernDashboardTab, 'refresh_data'):
            tab = ModernDashboardTab(
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
            
            # Mock refresh_data after initialization
            tab.refresh_data = Mock()
            
            # Simulate event
            with patch('PySide6.QtCore.QTimer.singleShot') as mock_timer:
                event = TicketCreatedEvent(ticket_id=1, user_id=1)
                tab._handle_domain_event(event)
                
                # Verify timer called
                mock_timer.assert_called_once()
                callback = mock_timer.call_args[0][1]
                assert callback == tab.refresh_data
