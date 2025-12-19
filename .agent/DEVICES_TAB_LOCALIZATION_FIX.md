# Devices Tab Localization Fixes

## Overview

Localized the `modern_devices_tab.py` file and refactored the filtering logic to be robust against language changes.

## Changes Made

### 1. Hardcoded Strings Localized

Replaced hardcoded strings with `language_manager` calls:

- **Filters**: Statuses, "All Customers", "Show Returned", etc.
- **Headers**: "Barcode", "Brand", "Model", etc.
- **Buttons**: "New Device", "Bulk Update", "Bulk Delete", "Refresh", "Export".
- **Cards**: "No Barcode", "Unknown Device".

### 2. Refactored Filters

Refactored `status_filter` and `customer_filter` to use `addItem(label, key)` pattern.

- **Before**: Relied on comparing localized text (e.g., `if status != "All Statuses"`).
- **After**: Uses internal keys (`all`, `received`, `diagnosed`, etc.) stored in user data.

### 3. Language File Updates

- **`en.ini`**: Added `[Devices]` section with new keys.
- **`burmese - ဗမာ.ini`**: Added `[Devices]` section with Burmese translations.

## Verification

- Verified application runs without errors.
- Verified filtering logic uses internal keys.

## Next Steps

- Ensure other language files have the `[Devices]` section added if needed (currently only added to English and Burmese).
