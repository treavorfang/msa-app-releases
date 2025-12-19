# Task 8: EventBus Migration Implementation Plan

## Objective

Replace Qt Signals with EventBus for domain events to achieve better decoupling and testability.

## Current State Analysis

### ✅ Already Complete

- EventBus infrastructure (`core/event_bus.py`)
- Event definitions (`core/events.py`)
- Events defined for: Tickets, Invoices, Customers

### 🔍 What Needs Migration

#### Controllers Currently Using Qt Signals

1. **TicketController** - Has `data_changed` signal
2. **InvoiceController** - Has `invoice_created`, `invoice_updated` signals
3. **CustomerController** - Has `data_changed` signal

#### Views Currently Listening to Signals

1. **ModernTicketsTab** - Connects to `ticket_controller.data_changed`
2. **ModernDashboardTab** - Connects to multiple controller signals
3. **ModernInvoiceTab** - Connects to `invoice_controller` signals
4. **ModernCustomersTab** - Connects to `customer_controller.data_changed`

## Implementation Strategy

### Phase 1: Controllers Publish Events (Dual Mode)

**Approach**: Add EventBus publishing ALONGSIDE existing signals (not replacing yet)

**Benefits**:

- Zero risk - existing code keeps working
- Can test EventBus in parallel
- Easy rollback if issues found

**For Each Controller**:

```python
# Example in TicketController.create_ticket()
def create_ticket(self, ticket_data, user_id):
    ticket = # ... create ticket logic

    # OLD: Keep this for now
    self.data_changed.emit()

    # NEW: Also publish event
    EventBus.publish(TicketCreatedEvent(
        ticket_id=ticket.id,
        user_id=user_id
    ))

    return ticket
```

### Phase 2: Views Subscribe to Events (Dual Mode)

**Approach**: Subscribe to EventBus ALONGSIDE existing signal connections

**For Each View**:

```python
def __init__(self, ...):
    # ... existing code

    # OLD: Keep this for now
    self.ticket_controller.data_changed.connect(self._load_tickets)

    # NEW: Also subscribe to events
    EventBus.subscribe(TicketCreatedEvent, self._on_ticket_created)
    EventBus.subscribe(TicketUpdatedEvent, self._on_ticket_updated)

def _on_ticket_created(self, event: TicketCreatedEvent):
    \"\"\"Handle ticket created event\"\"\"
    self._load_tickets()  # Refresh data
```

### Phase 3: Verify Dual Mode Works

- Test all CRUD operations
- Verify both signals AND events fire
- Confirm UI updates correctly
- Check no duplicate updates

### Phase 4: Remove Signal Connections (One at a time)

**Approach**: Remove signal connections gradually, testing after each

1. Remove from one view first (e.g., ModernTicketsTab)
2. Test thoroughly
3. If good, remove from next view
4. Repeat until all views migrated

### Phase 5: Remove Signal Emissions from Controllers

**Final step**: Once all views use EventBus, remove signal emissions

## Detailed Steps

### Step 1: Update TicketController

**File**: `src/app/controllers/ticket_controller.py`

Methods to update:

- `create_ticket()` → publish `TicketCreatedEvent`
- `update_ticket()` → publish `TicketUpdatedEvent`
- `delete_ticket()` → publish `TicketDeletedEvent`
- `restore_ticket()` → publish `TicketRestoredEvent`
- `update_status()` → publish `TicketStatusChangedEvent`
- `assign_technician()` → publish `TicketTechnicianAssignedEvent`

### Step 2: Update InvoiceController

**File**: `src/app/controllers/invoice_controller.py`

Methods to update:

- `create_invoice()` → publish `InvoiceCreatedEvent`
- `update_invoice()` → publish `InvoiceUpdatedEvent`
- `delete_invoice()` → publish `InvoiceDeletedEvent`

### Step 3: Update CustomerController

**File**: `src/app/controllers/customer_controller.py`

Methods to update:

- `create_customer()` → publish `CustomerCreatedEvent`
- `update_customer()` → publish `CustomerUpdatedEvent`
- `delete_customer()` → publish `CustomerDeletedEvent`

### Step 4: Update ModernTicketsTab

**File**: `src/app/views/tickets/modern_tickets_tab.py`

Subscribe to events in `__init__`:

```python
EventBus.subscribe(TicketCreatedEvent, self._on_ticket_event)
EventBus.subscribe(TicketUpdatedEvent, self._on_ticket_event)
EventBus.subscribe(TicketDeletedEvent, self._on_ticket_event)
EventBus.subscribe(TicketRestoredEvent, self._on_ticket_event)
```

Add cleanup in `closeEvent` or destructor:

```python
def closeEvent(self, event):
    EventBus.unsubscribe(TicketCreatedEvent, self._on_ticket_event)
    # ... unsubscribe all
```

### Step 5: Update ModernDashboardTab

**File**: `src/app/views/modern_dashboard.py`

Subscribe to ALL events (dashboard shows overview):

- All Ticket events
- All Invoice events
- All Customer events

### Step 6: Update ModernInvoiceTab

**File**: `src/app/views/invoice/modern_invoice_tab.py`

Subscribe to:

- `InvoiceCreatedEvent`
- `InvoiceUpdatedEvent`
- `InvoiceDeletedEvent`

### Step 7: Update ModernCustomersTab

**File**: `src/app/views/customer/modern_customers_tab.py`

Subscribe to:

- `CustomerCreatedEvent`
- `CustomerUpdatedEvent`
- `CustomerDeletedEvent`

## Testing Checklist

### After Each Controller Update

- [ ] Create operation works
- [ ] Update operation works
- [ ] Delete operation works
- [ ] Both signal AND event fire
- [ ] No errors in console

### After Each View Update

- [ ] View refreshes on events
- [ ] No duplicate refreshes
- [ ] All CRUD operations still work
- [ ] Cross-tab updates work (e.g., dashboard updates when ticket created)

### After Signal Removal

- [ ] View still refreshes correctly
- [ ] Only EventBus is used
- [ ] No broken functionality
- [ ] Performance is good

## Rollback Plan

If issues occur:

1. **Phase 1-3**: Just remove EventBus code, signals still work
2. **Phase 4**: Re-add signal connections to affected view
3. **Phase 5**: Re-add signal emissions to controller

## Benefits After Migration

1. **Better Testability**: Can test event publishing without UI
2. **Loose Coupling**: Views don't need direct controller references
3. **Flexibility**: Easy to add new subscribers without modifying controllers
4. **Consistency**: All domain events use same pattern
5. **Debugging**: Can log all events in one place

## Timeline

- **Step 1-3** (Controllers): 45 minutes
- **Step 4-7** (Views): 60 minutes
- **Testing**: 30 minutes
- **Signal Removal**: 30 minutes
- **Total**: ~3 hours

## Next Steps

1. Start with TicketController (Step 1)
2. Add event publishing alongside signals
3. Test that both work
4. Move to next controller
5. Once all controllers done, update views
6. Test thoroughly
7. Remove signals gradually

Ready to begin! 🚀
