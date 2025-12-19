"""
Shared pytest fixtures for all tests
"""

import pytest
from unittest.mock import Mock
import sys
import os

# Add src/app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'app'))


@pytest.fixture
def mock_user():
    """Create a mock user"""
    user = Mock()
    user.id = 1
    user.username = "test_user"
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_ticket_service():
    """Create a properly mocked ticket service"""
    service = Mock()
    service.get_ticket_statistics.return_value = {
        'total': 10,
        'open': 5,
        'in_progress': 2,
        'completed': 3
    }
    service.get_dashboard_stats_range.return_value = {
        'total': 10,
        'open': 5,
        'completed': 3,
        'cancelled': 2,
        'revenue': 1000.0
    }
    service.list_tickets.return_value = []
    service.calculate_average_completion_time.return_value = 24.5
    return service


@pytest.fixture
def mock_ticket_controller():
    """Create a mock ticket controller"""
    controller = Mock()
    controller.list_tickets.return_value = []
    return controller


@pytest.fixture
def mock_invoice_controller():
    """Create a mock invoice controller"""
    controller = Mock()
    controller.list_invoices.return_value = []
    return controller


@pytest.fixture
def mock_customer_controller():
    """Create a mock customer controller"""
    controller = Mock()
    controller.get_all_customers.return_value = []
    return controller


@pytest.fixture
def mock_technician_controller():
    """Create a mock technician controller"""
    return Mock()


@pytest.fixture
def mock_technician_repository():
    """Create a mock technician repository"""
    repo = Mock()
    repo.get_all_technicians.return_value = []
    return repo


@pytest.fixture
def mock_repair_part_controller():
    """Create a mock repair part controller"""
    return Mock()


@pytest.fixture
def mock_work_log_controller():
    """Create a mock work log controller"""
    return Mock()


@pytest.fixture
def mock_business_settings_service():
    """Create a mock business settings service"""
    return Mock()


@pytest.fixture
def mock_part_service():
    """Create a mock part service"""
    return Mock()
