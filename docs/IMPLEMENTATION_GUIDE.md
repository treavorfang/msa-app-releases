# Implementation Guide: Dependency Injection Pattern

## Quick Reference

This guide shows you how to apply the new dependency injection pattern when creating or modifying components.

---

## Pattern: Constructor Injection

### ✅ DO THIS (New Pattern)

```python
class MyNewTab(QWidget):
    def __init__(self,
                 required_service,
                 required_controller,
                 user,
                 optional_service=None,
                 container=None):  # Keep for legacy child components
        """
        Initialize MyNewTab with explicit dependencies.

        Args:
            required_service: Service for doing X
            required_controller: Controller for managing Y
            user: Current user context
            optional_service: Optional service for Z
            container: Legacy support (will be removed in future)
        """
        super().__init__()

        # Store dependencies
        self.required_service = required_service
        self.required_controller = required_controller
        self.user = user
        self.optional_service = optional_service
        self.container = container  # Legacy only

        self._setup_ui()
```

### ❌ DON'T DO THIS (Old Pattern)

```python
class MyNewTab(QWidget):
    def __init__(self, container, user):
        """Initialize with container (OLD PATTERN - DON'T USE)"""
        super().__init__()

        self.container = container
        self.user = user

        # Hidden dependencies - unclear what this component needs
        self.required_service = container.required_service
        self.required_controller = container.required_controller
```

---

## When to Use Each Dependency Type

### Required Dependencies

Pass as **positional arguments** (no default value):

```python
def __init__(self, ticket_service, user):
    """ticket_service and user are REQUIRED"""
```

Use for:

- Core services the component can't function without
- User context
- Primary controllers

### Optional Dependencies

Pass as **keyword arguments** with `None` default:

```python
def __init__(self, ticket_service, user, invoice_controller=None):
    """invoice_controller is OPTIONAL"""
```

Use for:

- Features that may not be available in all contexts
- Services used only in specific scenarios
- Cross-cutting concerns

### Legacy Container

Always pass as **last parameter** with `None` default:

```python
def __init__(self, ticket_service, user, container=None):
    """container is for LEGACY SUPPORT ONLY"""
```

Use for:

- Backward compatibility
- Child dialogs that haven't been refactored yet
- Temporary migration period

---

## Instantiation Patterns

### In Parent Component (Composition Root)

```python
class MainWindow(QMainWindow):
    def _setup_ui(self):
        # ✅ GOOD: Explicit dependency passing
        self.tickets_tab = ModernTicketsTab(
            ticket_controller=self.container.ticket_controller,
            technician_controller=self.container.technician_controller,
            ticket_service=self.container.ticket_service,
            business_settings_service=self.container.business_settings_service,
            user=self.user,
            invoice_controller=self.container.invoice_controller,
            container=self.container  # Legacy support
        )

        # ❌ BAD: Passing entire container
        self.tickets_tab = ModernTicketsTab(self.container, self.user)
```

### In Child Dialog

```python
class MyTab(QWidget):
    def _show_details_dialog(self, item):
        # ✅ GOOD: Pass only what the dialog needs
        dialog = DetailsDialog(
            item=item,
            item_service=self.item_service,
            item_controller=self.item_controller,
            user=self.user,
            container=self.container  # For legacy child dialogs
        )
        dialog.exec()

        # ❌ BAD: Pass container
        dialog = DetailsDialog(item, self.container, self.user)
```

---

## Using Dependencies

### ✅ DO THIS

```python
class MyTab(QWidget):
    def __init__(self, ticket_service, user):
        self.ticket_service = ticket_service
        self.user = user

    def load_data(self):
        # Direct access to injected dependency
        tickets = self.ticket_service.get_all_tickets()
        self._display_tickets(tickets)
```

### ❌ DON'T DO THIS

```python
class MyTab(QWidget):
    def __init__(self, container, user):
        self.container = container
        self.user = user

    def load_data(self):
        # Accessing via container
        tickets = self.container.ticket_service.get_all_tickets()
        self._display_tickets(tickets)
```

---

## Handling Optional Dependencies

### Pattern 1: Check Before Use

```python
class MyTab(QWidget):
    def __init__(self, required_service, optional_service=None):
        self.required_service = required_service
        self.optional_service = optional_service

    def do_something(self):
        # Always available
        self.required_service.do_required_thing()

        # Check before use
        if self.optional_service:
            self.optional_service.do_optional_thing()
```

### Pattern 2: Provide Default Behavior

```python
class MyTab(QWidget):
    def __init__(self, required_service, optional_service=None):
        self.required_service = required_service
        self.optional_service = optional_service or DefaultService()

    def do_something(self):
        # Always safe to call
        self.optional_service.do_thing()
```

---

## Testing with Mocks

### Before (Integration Test)

```python
def test_load_tickets():
    # Slow: Initializes entire container
    container = DependencyContainer()
    tab = ModernTicketsTab(container, user)

    # Hard to control behavior
    tab._load_tickets()

    # Hard to verify specific calls
    assert len(tab.tickets) > 0
```

### After (Unit Test)

```python
from unittest.mock import Mock

def test_load_tickets():
    # Fast: Only mock what you need
    mock_ticket_service = Mock()
    mock_ticket_service.get_all_tickets.return_value = [
        TicketDTO(id=1, ticket_number="T001"),
        TicketDTO(id=2, ticket_number="T002"),
    ]

    tab = ModernTicketsTab(
        ticket_controller=Mock(),
        technician_controller=Mock(),
        ticket_service=mock_ticket_service,
        business_settings_service=Mock(),
        user=user
    )

    # Easy to control behavior
    tab._load_tickets()

    # Easy to verify specific calls
    mock_ticket_service.get_all_tickets.assert_called_once()
    assert len(tab.tickets) == 2
```

---

## Migration Checklist

When refactoring an existing component:

### Step 1: Update Constructor

- [ ] Add explicit parameters for each dependency
- [ ] Keep `container` parameter with `None` default
- [ ] Add comprehensive docstring

### Step 2: Update Initialization

- [ ] Assign dependencies to instance variables
- [ ] Remove `self.x = container.x` patterns

### Step 3: Update Usage

- [ ] Replace `self.container.service` with `self.service`
- [ ] Remove unnecessary `if self.container:` checks
- [ ] Update conditional logic for optional dependencies

### Step 4: Update Call Sites

- [ ] Find all places where component is instantiated
- [ ] Pass explicit dependencies instead of container
- [ ] Keep container for backward compatibility

### Step 5: Test

- [ ] Verify existing functionality works
- [ ] Add unit tests with mocks
- [ ] Check for any missed container references

---

## Common Patterns

### Pattern: Service + Controller Pair

Many components need both a service (business logic) and controller (orchestration):

```python
class MyTab(QWidget):
    def __init__(self,
                 my_service,      # Business logic
                 my_controller,   # Orchestration
                 user):
        self.my_service = my_service
        self.my_controller = my_controller
        self.user = user
```

### Pattern: Cross-Tab Communication

For components that need to interact with other tabs:

```python
class MyTab(QWidget):
    def __init__(self,
                 my_service,
                 my_controller,
                 user,
                 invoice_controller=None):  # Optional for creating invoices
        self.my_service = my_service
        self.my_controller = my_controller
        self.user = user
        self.invoice_controller = invoice_controller

    def create_invoice(self, item):
        if self.invoice_controller:
            self.invoice_controller.create_invoice(item)
        else:
            # Graceful degradation
            MessageHandler.show_warning(self, "Invoice feature not available")
```

### Pattern: Settings/Configuration

For components that need configuration:

```python
class MyTab(QWidget):
    def __init__(self,
                 my_service,
                 settings_service,  # For app settings
                 user):
        self.my_service = my_service
        self.settings_service = settings_service
        self.user = user

    def load_data(self):
        # Use settings to customize behavior
        page_size = self.settings_service.get('page_size', default=50)
        items = self.my_service.get_items(limit=page_size)
```

---

## Anti-Patterns to Avoid

### ❌ Passing Container to New Components

```python
# DON'T DO THIS
class NewFeature(QWidget):
    def __init__(self, container):
        self.container = container
```

### ❌ Accessing Container in Methods

```python
# DON'T DO THIS
class MyTab(QWidget):
    def do_something(self):
        service = self.container.some_service
        service.do_thing()
```

### ❌ Creating Services Inside Components

```python
# DON'T DO THIS
class MyTab(QWidget):
    def __init__(self):
        self.service = MyService()  # Hard to test, tight coupling
```

### ❌ Importing Container Directly

```python
# DON'T DO THIS
from core.dependency_container import container

class MyTab(QWidget):
    def do_something(self):
        container.some_service.do_thing()
```

---

## FAQ

**Q: Why not just pass the container? It's simpler.**
A: Passing the container hides dependencies and makes testing difficult. Explicit dependencies make code clearer and more maintainable.

**Q: What if I need many dependencies (10+)?**
A: This is a code smell. Consider:

1. Breaking the component into smaller pieces
2. Creating a facade service that combines related operations
3. Using a configuration object for related settings

**Q: When can I remove the container parameter?**
A: After all child components have been refactored to use explicit dependencies. Keep it for now for backward compatibility.

**Q: How do I handle circular dependencies?**
A: Use interfaces/protocols or event-driven communication (EventBus). If A needs B and B needs A, they're probably too tightly coupled.

**Q: Should I refactor all components at once?**
A: No. Refactor incrementally:

1. Start with leaf components (no children)
2. Move up to parent components
3. Update call sites as you go
4. Keep container for backward compatibility

---

## Examples from Codebase

### Example 1: ModernTicketsTab

**Before**:

```python
def __init__(self, container, user):
    self.container = container
    self.ticket_controller = container.ticket_controller
```

**After**:

```python
def __init__(self,
             ticket_controller,
             technician_controller,
             ticket_service,
             business_settings_service,
             user,
             invoice_controller=None,
             container=None):
    self.ticket_controller = ticket_controller
    self.technician_controller = technician_controller
    self.ticket_service = ticket_service
    self.business_settings_service = business_settings_service
    self.invoice_controller = invoice_controller
    self.user = user
    self.container = container
```

### Example 2: TicketDetailsDialog

**Before**:

```python
def __init__(self, ticket, container=None, user=None, parent=None):
    self.ticket = ticket
    self.container = container
    self.user = user
```

**After**:

```python
def __init__(self,
             ticket,
             ticket_service,
             ticket_controller,
             technician_controller,
             repair_part_controller,
             work_log_controller,
             business_settings_service,
             part_service,
             technician_repository,
             user,
             container=None,
             parent=None):
    self.ticket = ticket
    self.ticket_service = ticket_service
    self.ticket_controller = ticket_controller
    # ... etc
    self.container = container
```

---

## Resources

- [GOOGLE_3X_REFACTORING.md](./GOOGLE_3X_REFACTORING.md) - Full architecture overview
- [REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md) - Summary of changes made
- [Dependency Injection Principles](https://martinfowler.com/articles/injection.html)
- [Google's Testing Best Practices](https://testing.googleblog.com/)

---

**Last Updated**: 2025-12-03
**Status**: Active - Use this pattern for all new code
