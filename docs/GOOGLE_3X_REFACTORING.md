# Google 3X Architecture Refactoring

## Overview

This document outlines the architectural improvements applied to the MSA (Mobile Service Accounting) codebase following Google's **3X principles**: **Experience, Excellence, Execution**.

---

## 1. One Binary, Many Configs (Execution)

### Problem

Configuration was hardcoded and scattered across multiple files, making it impossible to deploy the same binary to different environments (dev, staging, prod).

### Solution

**Status**: Foundation laid, full implementation pending

#### Implemented

- Created `core/event_bus.py` for decoupled event-driven architecture
- Created `core/events.py` with domain events (TicketCreatedEvent, TicketUpdatedEvent, etc.)

#### Next Steps

```python
# TODO: Implement flag-based configuration using absl-py
# src/app/main.py (Future)
from absl import app, flags

FLAGS = flags.FLAGS
flags.DEFINE_string('env', 'dev', 'Environment: dev, prod, staging')
flags.DEFINE_string('db_path', 'msa.db', 'Path to database')
flags.DEFINE_boolean('debug_ui', False, 'Enable UI debugging tools')

def main(argv):
    config = load_config(env=FLAGS.env, db_path=FLAGS.db_path)
    msa_app = MSA(config=config)
    sys.exit(msa_app.run())
```

**Benefits**:

- Same binary can be deployed to dev/staging/prod
- Configuration changes don't require recompilation
- Easier testing with different configurations

---

## 2. Modular Boundaries (Excellence)

### Problem

The `DependencyContainer` was a "God Object" that created tight coupling:

- Views imported the entire container
- Circular dependencies everywhere
- Impossible to test components in isolation

### Solution: Explicit Dependency Injection

#### Before (Bad)

```python
class ModernTicketsTab(TicketBaseWidget):
    def __init__(self, container, user):
        self.container = container
        self.ticket_controller = container.ticket_controller
        # Implicitly depends on EVERYTHING in container
```

#### After (Good)

```python
class ModernTicketsTab(TicketBaseWidget):
    def __init__(self,
                 ticket_controller,
                 technician_controller,
                 ticket_service,
                 business_settings_service,
                 user,
                 invoice_controller=None,
                 container=None):  # Legacy support
        """
        Initialize with explicit dependencies (Google 3X: Excellence).

        Dependencies are now visible in the signature.
        Container is kept for legacy child dialogs only.
        """
        self.ticket_controller = ticket_controller
        self.technician_controller = technician_controller
        # ... explicit assignments
```

#### Benefits

- **Clarity**: Dependencies are explicit in the constructor
- **Testability**: Can inject mocks for testing
- **Maintainability**: Easy to see what a component actually needs
- **Decoupling**: Components don't know about the entire system

### Proposed Module Structure (Future)

```
//msa/data        - Models, DTOs, Repositories (No UI dependencies)
//msa/domain      - Business Services, Logic (Depends on //msa/data)
//msa/api         - Abstract Interfaces/Protocols for Controllers
//msa/ui          - Views and Widgets (Depends ONLY on //msa/api and DTOs)
//msa/main        - Composition Root (The ONLY place that wires everything)
```

---

## 3. Event-Driven Architecture (Excellence)

### Problem

Direct signal/slot connections created tight coupling:

```python
# Before: Direct coupling
self.ticket_controller.ticket_created.connect(self._on_ticket_changed)
self.ticket_controller.ticket_updated.connect(self._on_ticket_changed)
# ... dozens of connections across the codebase
```

As the app grows, tracking who listens to what becomes impossible.

### Solution: Pub/Sub Event Bus

#### Implementation

```python
# core/event_bus.py
class EventBus:
    """
    A simple Publish/Subscribe event bus to decouple components.
    Follows Google's 'Excellence' principle by reducing direct coupling.
    """
    _subscribers: Dict[Type[Event], List[Callable[[Event], None]]] = defaultdict(list)

    @classmethod
    def subscribe(cls, event_type: Type[Event], handler: Callable[[Event], None]):
        """Subscribe a handler to a specific event type."""
        cls._subscribers[event_type].append(handler)

    @classmethod
    def publish(cls, event: Event):
        """Publish an event to all subscribers."""
        for handler in cls._subscribers[type(event)]:
            try:
                handler(event)
            except Exception as e:
                print(f"Error handling event {event}: {e}")
```

#### Usage Pattern

**Publisher (Controller)**:

```python
from core.event_bus import EventBus
from core.events import TicketCreatedEvent

def create_ticket(self, ...):
    # ... business logic ...
    EventBus.publish(TicketCreatedEvent(
        ticket_id=ticket.id,
        user_id=user.id
    ))
```

**Subscriber (View)**:

```python
from core.event_bus import EventBus
from core.events import TicketCreatedEvent

class ModernTicketsTab(TicketBaseWidget):
    def __init__(self, ...):
        super().__init__()
        EventBus.subscribe(TicketCreatedEvent, self._on_ticket_created)

    def _on_ticket_created(self, event: TicketCreatedEvent):
        self._load_tickets()
```

#### Benefits

- **Decoupling**: Publishers don't know about subscribers
- **Scalability**: Easy to add new listeners without modifying existing code
- **Debugging**: Centralized event flow makes debugging easier
- **Testing**: Can verify events are published without full integration tests

---

## 4. Dependency Injection Framework (Execution)

### Current State

We're using **Constructor Injection** manually. This is a good first step.

### Future: Lightweight DI Framework

For a production Google-scale system, we'd use a DI framework like `pinject`:

```python
# di_module.py (Future)
import pinject

class MsaModule(pinject.BindingSpec):
    def configure(self, bind):
        # Bind Interfaces to Implementations
        bind('ticket_repository', to_class=SqlTicketRepository)
        bind('ticket_service', to_class=TicketServiceImpl)

    def provide_db_connection(self):
        # Provider method for complex objects
        return create_db_connection(FLAGS.db_path)

# main.py
def main():
    obj_graph = pinject.new_object_graph(modules=[MsaModule()])
    app = obj_graph.provide(MSA)
    app.run()
```

**Benefits**:

- Automatic dependency resolution
- Singleton management
- Easier to swap implementations (e.g., for testing)

---

## Refactoring Progress

### ✅ Completed

1. **ModernTicketsTab** - Refactored to use explicit dependencies
2. **TicketDetailsDialog** - Refactored to use explicit dependencies
3. **MainWindow** - Updated to pass explicit dependencies to ModernTicketsTab
4. **EventBus** - Created foundational event system
5. **Domain Events** - Defined ticket-related events

### 🚧 In Progress

- Updating other call sites for TicketDetailsDialog
- Migrating from PySide6 signals to EventBus

### 📋 TODO

1. **Refactor remaining views**:

   - `ModernDashboardTab`
   - `ModernInvoiceTab`
   - `ModernCustomersTab`
   - `ModernDevicesTab`
   - `ModernInventoryTab`

2. **Implement EventBus throughout**:

   - Replace all `ticket_controller.ticket_created.connect()` with EventBus
   - Replace all `invoice_controller.invoice_created.connect()` with EventBus
   - Add events for all domain actions

3. **Configuration Management**:

   - Install `absl-py`
   - Implement flag-based configuration
   - Create environment-specific config files

4. **Dependency Injection**:

   - Evaluate `pinject` or similar lightweight DI framework
   - Create DI modules for each layer
   - Remove manual wiring from MainWindow

5. **Module Boundaries**:
   - Reorganize code into clear layers (data, domain, api, ui)
   - Define visibility rules (e.g., UI can't import from data directly)
   - Create interface/protocol definitions

---

## Testing Strategy

### Before Refactoring

```python
# Impossible to test without full app context
def test_ticket_tab():
    container = DependencyContainer()  # Initializes EVERYTHING
    tab = ModernTicketsTab(container, user)
    # Test is slow and brittle
```

### After Refactoring

```python
# Fast, isolated unit tests
def test_ticket_tab():
    mock_ticket_controller = Mock()
    mock_ticket_service = Mock()

    tab = ModernTicketsTab(
        ticket_controller=mock_ticket_controller,
        ticket_service=mock_ticket_service,
        # ... other mocks
    )

    # Fast, isolated test
    tab._load_tickets()
    mock_ticket_service.get_all_tickets.assert_called_once()
```

---

## Migration Guide

### For New Components

Always use explicit dependency injection:

```python
class NewFeatureTab(QWidget):
    def __init__(self,
                 required_service,
                 required_controller,
                 user,
                 optional_service=None):
        """
        Args:
            required_service: Service for X
            required_controller: Controller for Y
            user: Current user context
            optional_service: Optional service for Z
        """
        self.required_service = required_service
        # ...
```

### For Existing Components

1. Add new constructor with explicit dependencies
2. Keep `container` parameter for backward compatibility
3. Mark container as deprecated in docstring
4. Update call sites gradually
5. Remove container parameter once all call sites are updated

---

## Performance Considerations

### EventBus

- Currently synchronous (executes on UI thread)
- For production, consider:
  - Async event processing with `asyncio`
  - Event queue with worker threads
  - Event persistence for audit trail

### Dependency Injection

- Constructor injection has zero runtime overhead
- DI frameworks like `pinject` have minimal overhead
- Singleton management prevents duplicate instances

---

## References

- [Google's Monorepo Best Practices](https://abseil.io/resources/swe-book/html/ch16.html)
- [Dependency Injection Principles](https://martinfowler.com/articles/injection.html)
- [Event-Driven Architecture](https://martinfowler.com/articles/201701-event-driven.html)
- [Python Dependency Injection with Pinject](https://github.com/google/pinject)

---

## Questions & Answers

**Q: Why keep the `container` parameter?**
A: Backward compatibility. Some child dialogs still expect it. We'll remove it in a future phase.

**Q: When should I use EventBus vs. Qt Signals?**
A: Use EventBus for domain events (business logic). Use Qt Signals for UI events (button clicks, etc.).

**Q: Is this over-engineering for a small app?**
A: These patterns scale. They make the codebase maintainable as it grows. The initial investment pays off quickly.

---

**Last Updated**: 2025-12-03
**Author**: Google 3X Architecture Review
**Status**: Phase 1 Complete (Foundation)
