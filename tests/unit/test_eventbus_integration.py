"""
Comprehensive unit tests for EventBus integration.

Tests the complete EventBus flow:
- Controllers publishing events
- Views subscribing to events
- Event propagation
- Cross-component communication
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtWidgets import QApplication
import sys

from core.event_bus import EventBus
from core.events import (
    TicketCreatedEvent, TicketUpdatedEvent, TicketDeletedEvent,
    InvoiceCreatedEvent, DeviceCreatedEvent, PaymentCreatedEvent,
    CustomerCreatedEvent, TechnicianCreatedEvent
)

# Ensure QApplication exists
if not QApplication.instance():
    app = QApplication(sys.argv)


class TestEventBusCore:
    """Test core EventBus functionality"""
    
    def setup_method(self):
        """Clear EventBus before each test"""
        EventBus.clear()
    
    def test_subscribe_and_publish(self):
        """Test basic subscribe and publish"""
        handler = Mock()
        EventBus.subscribe(TicketCreatedEvent, handler)
        
        event = TicketCreatedEvent(ticket_id=1, user_id=1)
        EventBus.publish(event)
        
        handler.assert_called_once_with(event)
    
    def test_multiple_subscribers(self):
        """Test multiple handlers can subscribe to same event"""
        handler1 = Mock()
        handler2 = Mock()
        
        EventBus.subscribe(TicketCreatedEvent, handler1)
        EventBus.subscribe(TicketCreatedEvent, handler2)
        
        event = TicketCreatedEvent(ticket_id=1, user_id=1)
        EventBus.publish(event)
        
        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)
    
    def test_unsubscribe(self):
        """Test unsubscribing from events"""
        handler = Mock()
        EventBus.subscribe(TicketCreatedEvent, handler)
        EventBus.unsubscribe(TicketCreatedEvent, handler)
        
        event = TicketCreatedEvent(ticket_id=1, user_id=1)
        EventBus.publish(event)
        
        handler.assert_not_called()
    
    def test_different_event_types_isolated(self):
        """Test different event types don't interfere"""
        ticket_handler = Mock()
        invoice_handler = Mock()
        
        EventBus.subscribe(TicketCreatedEvent, ticket_handler)
        EventBus.subscribe(InvoiceCreatedEvent, invoice_handler)
        
        EventBus.publish(TicketCreatedEvent(ticket_id=1, user_id=1))
        
        ticket_handler.assert_called_once()
        invoice_handler.assert_not_called()


class TestControllerEventPublishing:
    """Test that controllers properly publish events"""
    
    def setup_method(self):
        """Clear EventBus before each test"""
        EventBus.clear()
    
    def test_ticket_controller_publishes_created_event(self):
        """Test TicketController publishes TicketCreatedEvent"""
        from controllers.ticket_controller import TicketController
        
        # Mock container and service
        mock_container = Mock()
        mock_service = Mock()
        mock_ticket = Mock()
        mock_ticket.id = 1
        mock_service.create_ticket.return_value = mock_ticket
        mock_container.ticket_service = mock_service
        
        controller = TicketController(mock_container)
        
        # Subscribe to event
        handler = Mock()
        EventBus.subscribe(TicketCreatedEvent, handler)
        
        # Create ticket
        controller.create_ticket({'title': 'Test'}, current_user=Mock(id=1), ip_address='127.0.0.1')
        
        # Verify event was published
        handler.assert_called_once()
        event = handler.call_args[0][0]
        assert isinstance(event, TicketCreatedEvent)
        assert event.ticket_id == 1
    
    def test_device_controller_publishes_created_event(self):
        """Test DeviceController publishes DeviceCreatedEvent"""
        from controllers.device_controller import DeviceController
        
        mock_container = Mock()
        mock_service = Mock()
        mock_device = Mock()
        mock_device.id = 1
        mock_service.create_device.return_value = mock_device
        mock_container.device_service = mock_service
        
        controller = DeviceController(mock_container)
        
        handler = Mock()
        EventBus.subscribe(DeviceCreatedEvent, handler)
        
        controller.create_device({'brand': 'Apple'}, current_user=Mock(id=1), ip_address='127.0.0.1')
        
        handler.assert_called_once()
        event = handler.call_args[0][0]
        assert isinstance(event, DeviceCreatedEvent)
        assert event.device_id == 1
    
    def test_payment_controller_publishes_created_event(self):
        """Test PaymentController publishes PaymentCreatedEvent"""
        from controllers.payment_controller import PaymentController
        
        mock_container = Mock()
        mock_service = Mock()
        mock_payment = Mock()
        mock_payment.id = 1
        mock_service.create_payment.return_value = mock_payment
        mock_container.payment_service = mock_service
        
        controller = PaymentController(mock_container)
        
        handler = Mock()
        EventBus.subscribe(PaymentCreatedEvent, handler)
        
        controller.create_payment({'amount': 100})
        
        handler.assert_called_once()
        event = handler.call_args[0][0]
        assert isinstance(event, PaymentCreatedEvent)
        assert event.payment_id == 1
    
    def test_technician_controller_publishes_created_event(self):
        """Test TechnicianController publishes TechnicianCreatedEvent"""
        from controllers.technician_controller import TechnicianController
        
        mock_container = Mock()
        mock_service = Mock()
        mock_technician = Mock()
        mock_technician.id = 1
        mock_service.create_technician.return_value = mock_technician
        mock_container.technician_service = mock_service
        # Mock current_user for event publishing
        mock_container.current_user = Mock(id=1)
        
        controller = TechnicianController(mock_container)
        
        handler = Mock()
        EventBus.subscribe(TechnicianCreatedEvent, handler)
        
        controller.create_technician({'name': 'John'})
        
        handler.assert_called_once()
        event = handler.call_args[0][0]
        assert isinstance(event, TechnicianCreatedEvent)
        assert event.technician_id == 1


class TestCrossComponentCommunication:
    """Test EventBus enables cross-component communication"""
    
    def setup_method(self):
        """Clear EventBus before each test"""
        EventBus.clear()
    
    def test_ticket_creation_triggers_dashboard_refresh(self):
        """Test creating ticket triggers dashboard to refresh"""
        # Simulate dashboard subscribing
        dashboard_refresh = Mock()
        EventBus.subscribe(TicketCreatedEvent, dashboard_refresh)
        
        # Simulate ticket creation
        EventBus.publish(TicketCreatedEvent(ticket_id=1, user_id=1))
        
        # Dashboard should be notified
        dashboard_refresh.assert_called_once()
    
    def test_invoice_creation_triggers_multiple_views(self):
        """Test invoice creation can trigger multiple views"""
        invoice_tab_refresh = Mock()
        customer_tab_refresh = Mock()
        dashboard_refresh = Mock()
        
        EventBus.subscribe(InvoiceCreatedEvent, invoice_tab_refresh)
        EventBus.subscribe(InvoiceCreatedEvent, customer_tab_refresh)
        EventBus.subscribe(InvoiceCreatedEvent, dashboard_refresh)
        
        EventBus.publish(InvoiceCreatedEvent(invoice_id=1, user_id=1))
        
        invoice_tab_refresh.assert_called_once()
        customer_tab_refresh.assert_called_once()
        dashboard_refresh.assert_called_once()
    
    def test_event_data_preserved_across_subscribers(self):
        """Test event data is correctly passed to all subscribers"""
        handler1 = Mock()
        handler2 = Mock()
        
        EventBus.subscribe(TicketCreatedEvent, handler1)
        EventBus.subscribe(TicketCreatedEvent, handler2)
        
        event = TicketCreatedEvent(ticket_id=42, user_id=7)
        EventBus.publish(event)
        
        # Both handlers should receive the same event with same data
        assert handler1.call_args[0][0].ticket_id == 42
        assert handler1.call_args[0][0].user_id == 7
        assert handler2.call_args[0][0].ticket_id == 42
        assert handler2.call_args[0][0].user_id == 7


class TestEventBusErrorHandling:
    """Test EventBus handles errors gracefully"""
    
    def setup_method(self):
        """Clear EventBus before each test"""
        EventBus.clear()
    
    def test_handler_exception_doesnt_stop_other_handlers(self):
        """Test one handler failing doesn't prevent others from running"""
        def failing_handler(event):
            raise Exception("Handler failed!")
        
        working_handler = Mock()
        
        EventBus.subscribe(TicketCreatedEvent, failing_handler)
        EventBus.subscribe(TicketCreatedEvent, working_handler)
        
        # Publish event - should not raise exception
        EventBus.publish(TicketCreatedEvent(ticket_id=1, user_id=1))
        
        # Working handler should still be called
        working_handler.assert_called_once()
    
    def test_unsubscribe_nonexistent_handler(self):
        """Test unsubscribing non-existent handler doesn't error"""
        handler = Mock()
        
        # Should not raise exception
        EventBus.unsubscribe(TicketCreatedEvent, handler)
    
    def test_publish_with_no_subscribers(self):
        """Test publishing with no subscribers doesn't error"""
        # Should not raise exception
        EventBus.publish(TicketCreatedEvent(ticket_id=1, user_id=1))


class TestEventBusPerformance:
    """Test EventBus performance characteristics"""
    
    def setup_method(self):
        """Clear EventBus before each test"""
        EventBus.clear()
    
    def test_many_subscribers_performance(self):
        """Test EventBus handles many subscribers efficiently"""
        import time
        
        # Add 100 subscribers
        handlers = [Mock() for _ in range(100)]
        for handler in handlers:
            EventBus.subscribe(TicketCreatedEvent, handler)
        
        # Measure publish time
        start = time.time()
        EventBus.publish(TicketCreatedEvent(ticket_id=1, user_id=1))
        duration = time.time() - start
        
        # Should complete quickly (< 100ms)
        assert duration < 0.1
        
        # All handlers should be called
        for handler in handlers:
            handler.assert_called_once()
    
    def test_many_events_performance(self):
        """Test EventBus handles many events efficiently"""
        import time
        
        handler = Mock()
        EventBus.subscribe(TicketCreatedEvent, handler)
        
        # Publish 1000 events
        start = time.time()
        for i in range(1000):
            EventBus.publish(TicketCreatedEvent(ticket_id=i, user_id=1))
        duration = time.time() - start
        
        # Should complete quickly (< 500ms)
        assert duration < 0.5
        
        # Handler should be called 1000 times
        assert handler.call_count == 1000


# Run tests if executed directly
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
