# Localization Bug Fix - Status Stored in Wrong Language

## Issue

When updating ticket status from the UI in Burmese language, the status was being stored in Burmese in the database instead of English. This caused data integrity issues and broke status-based logic.

### Root Cause

The status combo boxes were using `addItems()` with localized text, and then retrieving the selected value using `currentText().lower().replace(' ', '_')`. This meant:

- Display text: "ပြီးစီးပြီ" (Burmese for "Completed")
- Stored in DB: "ပြီးစီးပြီ" (wrong!)
- Should be: "completed" (English)

## Files Fixed

### 1. `ticket_details_dialog.py` (Lines 484-536)

**Before:**

```python
status_combo.addItems([
    self.lm.get("Common.open", "Open"),
    self.lm.get("Common.completed", "Completed"),
    # ...
])
new_status = status_combo.currentText().lower().replace(' ', '_')
```

**After:**

```python
status_options = [
    ('open', self.lm.get("Common.open", "Open")),
    ('completed', self.lm.get("Common.completed", "Completed")),
    # ...
]
for status_key, status_label in status_options:
    status_combo.addItem(status_label, status_key)  # Display text, stored data

new_status = status_combo.currentData()  # Gets English key
```

### 2. `tickets.py` (Lines 391-444)

Applied the same fix to the `_show_update_ticket_dialog()` method.

### 3. `modern_tickets_tab.py` ✅

Already correctly implemented - no changes needed!

## Solution Pattern

The correct pattern for localized combo boxes with database values:

```python
# Define options as (key, label) tuples
options = [
    ('english_key', self.lm.get("Translation.key", "Default Text")),
    # ...
]

# Add items with data
for key, label in options:
    combo.addItem(label, key)  # Display localized, store English

# Retrieve English value
english_value = combo.currentData()  # NOT currentText()

# Preselect by English value
index = combo.findData(current_english_value)
if index >= 0:
    combo.setCurrentIndex(index)
```

## Benefits

1. **Data Integrity**: Database always contains English status values
2. **Consistency**: Status logic works regardless of UI language
3. **Maintainability**: Status values are standardized across the system
4. **User Experience**: Users still see localized text in the UI

## Testing Checklist

- [x] Change language to Burmese
- [x] Update ticket status to "Completed" (ပြီးစီးပြီ)
- [x] Verify database stores "completed" (not Burmese text)
- [x] Verify UI displays Burmese text correctly
- [x] Verify status-based logic works (work log stops, invoice button enables)
- [x] Test all status values: open, diagnosed, in_progress, awaiting_parts, completed, cancelled, unrepairable

## Related Issues Fixed

This fix also ensures that:

- Work log auto-stop works correctly (checks for 'completed' status)
- Invoice button enabling works correctly (checks for 'completed', 'cancelled', 'unrepairable')
- Status filters work correctly
- Status-based reports work correctly
