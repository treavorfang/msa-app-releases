# Ticket Status Change - Work Log and Invoice Button Fix

## Issue

When updating a ticket status to "completed":

1. Work logs should stop automatically ✅ (Already working)
2. "Create Invoice" button should be enabled ❌ (Was not working)

## Root Cause

The `TicketDetailsDialog` was closing immediately after status update (`self.accept()`), preventing the UI from reflecting the new state. The "Create Invoice" button state was only set during initial dialog creation and never updated.

## Solution

### Changes Made to `ticket_details_dialog.py`:

1. **Store button as instance variable** (Line 129):

   - Changed from local `create_invoice_btn` to `self.create_invoice_btn`
   - This allows us to update the button state later

2. **Added `_update_create_invoice_button()` method** (Lines 590-604):

   - Checks ticket status and device status
   - Enables button only when status is 'completed', 'cancelled', or 'unrepairable'
   - Disables if invoice already created (device status == 'returned')
   - Updates tooltip accordingly

3. **Added `_refresh_ui()` method** (Lines 606-617):

   - Updates window title
   - Calls `_update_create_invoice_button()` to refresh button state
   - Can be extended to refresh other UI elements

4. **Modified `_update_ticket()` method** (Line 579):
   - Changed from `self.accept()` (close dialog) to `self._refresh_ui()` (refresh UI)
   - Dialog now stays open after status update, showing the new state

## Work Log Auto-Stop (Already Working)

The work log auto-stop functionality was already correctly implemented in `TicketService.change_ticket_status()`:

```python
# Automatically end work log when ticket is completed or cancelled
if new_status in ['completed', 'cancelled']:
    self._end_active_work_logs(ticket_id)
```

The `_end_active_work_logs()` method:

- Gets all work logs for the ticket
- Finds any with `end_time == null` (active logs)
- Sets their `end_time` to current datetime
- Handles errors gracefully without failing the status change

## Testing Checklist

- [ ] Change ticket status to "completed"
- [ ] Verify "Create Invoice" button becomes enabled
- [ ] Verify active work logs are stopped (end_time is set)
- [ ] Verify dialog stays open showing updated state
- [ ] Try creating an invoice - should work
- [ ] Verify button is disabled for statuses like "open", "in_progress"
- [ ] Verify button is disabled if invoice already created (device returned)

## Benefits

1. **Better UX**: User can immediately create invoice without closing/reopening dialog
2. **Immediate Feedback**: Button state updates instantly after status change
3. **Consistent State**: UI always reflects current ticket status
4. **No Data Loss**: Dialog stays open, preserving context
