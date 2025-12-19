# Task 9: Comprehensive Unit Tests - Implementation Plan

## Objective

Achieve >80% test coverage for refactored components with fast, isolated unit tests.

## Current Test Status

### Existing Tests (from Task 3)

**File**: `tests/test_modern_tickets_tab.py`

- ✅ 10 tests for ModernTicketsTab
- ✅ Tests use mocks
- ✅ Tests run fast

**File**: `tests/test_ticket_details_dialog.py`

- ✅ 8 tests for TicketDetailsDialog
- ✅ Tests use mocks
- ✅ Tests run fast

**File**: `tests/test_event_bus_migration.py`

- ✅ 5 tests for EventBus
- ✅ Tests event publishing/subscribing

**Total**: 23 tests ✅

## Components Needing Tests

### High Priority (Core Refactored Components)

#### 1. ModernDashboardTab

**File to create**: `tests/test_modern_dashboard_tab.py`

**Tests needed**:

- [ ] Test initialization with explicit DI
- [ ] Test data loading (tickets, invoices, customers)
- [ ] Test EventBus event handling
- [ ] Test summary card updates
- [ ] Test chart rendering (with matplotlib mocked)
- [ ] Test quick actions

**Estimated**: 8-10 tests

#### 2. ModernInvoiceTab

**File to create**: `tests/test_modern_invoice_tab.py`

**Tests needed**:

- [ ] Test initialization with explicit DI
- [ ] Test invoice loading
- [ ] Test filtering (status, overdue, cancelled)
- [ ] Test EventBus event handling
- [ ] Test invoice creation
- [ ] Test invoice updates
- [ ] Test payment recording
- [ ] Test export functionality

**Estimated**: 10-12 tests

#### 3. ModernCustomersTab

**File to create**: `tests/test_modern_customers_tab.py`

**Tests needed**:

- [ ] Test initialization with explicit DI
- [ ] Test customer loading
- [ ] Test filtering (balance, search)
- [ ] Test EventBus event handling
- [ ] Test customer creation
- [ ] Test customer updates
- [ ] Test balance calculation
- [ ] Test view switching (cards/list)

**Estimated**: 10-12 tests

#### 4. ModernDevicesTab

**File to create**: `tests/test_modern_devices_tab.py`

**Tests needed**:

- [ ] Test initialization
- [ ] Test device loading
- [ ] Test filtering (status, customer)
- [ ] Test device creation
- [ ] Test device updates
- [ ] Test bulk operations

**Estimated**: 8-10 tests

### Medium Priority (Controllers)

#### 5. TicketController

**File to create**: `tests/test_ticket_controller.py`

**Tests needed**:

- [ ] Test create_ticket publishes event
- [ ] Test update_ticket publishes event
- [ ] Test delete_ticket publishes event
- [ ] Test restore_ticket publishes event
- [ ] Test change_ticket_status publishes event
- [ ] Test assign_ticket publishes event

**Estimated**: 6-8 tests

#### 6. InvoiceController

**File to create**: `tests/test_invoice_controller.py`

**Tests needed**:

- [ ] Test create_invoice publishes event
- [ ] Test update_invoice publishes event
- [ ] Test delete_invoice publishes event
- [ ] Test invoice calculations

**Estimated**: 4-6 tests

#### 7. CustomerController

**File to create**: `tests/test_customer_controller.py`

**Tests needed**:

- [ ] Test create_customer publishes event
- [ ] Test update_customer publishes event
- [ ] Test delete_customer publishes event
- [ ] Test customer validation

**Estimated**: 4-6 tests

### Low Priority (Utilities & Services)

#### 8. EventBus (Already tested)

- ✅ 5 tests exist

#### 9. Language Manager

**File to create**: `tests/test_language_manager.py`

**Tests needed**:

- [ ] Test language loading
- [ ] Test key retrieval
- [ ] Test fallback behavior
- [ ] Test language switching

**Estimated**: 4-5 tests

## Testing Strategy

### 1. Use Mocks for All Dependencies

```python
from unittest.mock import Mock, MagicMock, patch

def test_modern_invoice_tab_initialization():
    # Mock all dependencies
    mock_invoice_controller = Mock()
    mock_ticket_controller = Mock()
    mock_user = Mock()

    # Create tab with mocked dependencies
    tab = ModernInvoiceTab(
        invoice_controller=mock_invoice_controller,
        ticket_controller=mock_ticket_controller,
        user=mock_user
    )

    # Assert initialization
    assert tab.invoice_controller == mock_invoice_controller
    assert tab.user == mock_user
```

### 2. Test EventBus Integration

```python
def test_customer_tab_handles_events():
    # Setup
    mock_controller = Mock()
    tab = ModernCustomersTab(
        customer_controller=mock_controller,
        invoice_controller=Mock(),
        user=Mock()
    )

    # Clear EventBus
    EventBus.clear()

    # Subscribe
    tab._connect_signals()

    # Publish event
    EventBus.publish(CustomerCreatedEvent(customer_id=1, user_id=1))

    # Assert handler was called (check if _load_customers was scheduled)
    # This is tricky with QTimer.singleShot, might need to mock QTimer
```

### 3. Test UI Components (Minimal)

```python
def test_invoice_tab_creates_ui_elements():
    tab = ModernInvoiceTab(Mock(), Mock(), Mock())

    # Assert key UI elements exist
    assert hasattr(tab, 'search_input')
    assert hasattr(tab, 'status_filter')
    assert hasattr(tab, 'invoices_table')
```

### 4. Test Business Logic

```python
def test_customer_balance_calculation():
    mock_invoice_controller = Mock()
    mock_invoice_controller.get_customer_invoices.return_value = [
        Mock(total=100, payment_status='unpaid'),
        Mock(total=50, payment_status='paid')
    ]

    tab = ModernCustomersTab(Mock(), mock_invoice_controller, Mock())
    balance = tab._calculate_customer_balance(customer_id=1)

    assert balance['total_owed'] == 100
```

## Test Organization

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py                          # Shared fixtures
├── test_event_bus_migration.py          # ✅ Exists
├── test_modern_tickets_tab.py           # ✅ Exists
├── test_ticket_details_dialog.py        # ✅ Exists
├── test_modern_dashboard_tab.py         # 📝 To create
├── test_modern_invoice_tab.py           # 📝 To create
├── test_modern_customers_tab.py         # 📝 To create
├── test_modern_devices_tab.py           # 📝 To create
├── test_ticket_controller.py            # 📝 To create
├── test_invoice_controller.py           # 📝 To create
├── test_customer_controller.py          # 📝 To create
└── test_language_manager.py             # 📝 To create
```

### Shared Fixtures (conftest.py)

```python
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_user():
    user = Mock()
    user.id = 1
    user.username = "test_user"
    return user

@pytest.fixture
def mock_ticket_controller():
    controller = Mock()
    controller.list_tickets.return_value = []
    return controller

@pytest.fixture
def mock_invoice_controller():
    controller = Mock()
    controller.list_invoices.return_value = []
    return controller

@pytest.fixture
def mock_customer_controller():
    controller = Mock()
    controller.get_all_customers.return_value = []
    return controller
```

## Execution Plan

### Phase 1: High Priority Views (2 hours)

1. ✅ Create `test_modern_dashboard_tab.py` (30 min)
2. ✅ Create `test_modern_invoice_tab.py` (30 min)
3. ✅ Create `test_modern_customers_tab.py` (30 min)
4. ✅ Create `test_modern_devices_tab.py` (30 min)

### Phase 2: Controllers (1 hour)

5. ✅ Create `test_ticket_controller.py` (20 min)
6. ✅ Create `test_invoice_controller.py` (20 min)
7. ✅ Create `test_customer_controller.py` (20 min)

### Phase 3: Utilities (30 min)

8. ✅ Create `test_language_manager.py` (30 min)

### Phase 4: Coverage & Cleanup (30 min)

9. ✅ Run coverage report
10. ✅ Identify gaps
11. ✅ Add missing tests
12. ✅ Update documentation

## Success Criteria

- ✅ >80% code coverage for refactored components
- ✅ All tests run in <2 seconds total
- ✅ All tests use mocks (no database access)
- ✅ Tests are isolated and independent
- ✅ CI/CD ready

## Commands

### Run All Tests

```bash
cd /Users/studiotai/PyProject/msa
python3 -m pytest tests/ -v
```

### Run with Coverage

```bash
python3 -m pytest tests/ --cov=src/app --cov-report=html --cov-report=term
```

### Run Specific Test File

```bash
python3 -m pytest tests/test_modern_invoice_tab.py -v
```

## Next Steps

1. Start with **Phase 1: ModernDashboardTab tests**
2. Create comprehensive test suite
3. Achieve >80% coverage
4. Document results

Ready to begin! 🧪
