# Invoice Tab Localization Fixes

## Overview

Checked and fixed localization issues in `modern_invoice_tab.py` to ensure all labels are properly localized and the code is robust against language changes.

## Changes Made

### 1. Hardcoded Strings Localized

Replaced hardcoded strings with `language_manager` calls:

- **Customer Name**: `"Unknown"` -> `self.lm.get("Common.unknown", "Unknown")`
- **Overdue Status**: `"Yes"/"No"` -> `self.lm.get("Common.yes", "Yes")` / `self.lm.get("Common.no", "No")`
- **Default Values**: `"N/A"` -> `self.lm.get("Common.na", "N/A")`
- **Service Description**: `"Service"` -> `self.lm.get("Invoices.service", "Service")`

### 2. Language File Updates

- **`en.ini`**: Added missing key `service = Service` under `[Invoices]`.
- **`burmese - ဗမာ.ini`**: Added missing key `service = ဝန်ဆောင်မှု` under `[Invoices]`.
- **`modern_invoice_tab.py`**: Updated to use `Common.na` instead of `Common.not_applicable` to match existing keys.

### 3. Refactored Status Filter

Refactored the status filter in `modern_invoice_tab.py` to use the robust `addItem(label, key)` pattern.

- **Before**: Relied on mapping localized text back to internal keys (fragile).
- **After**: Stores internal keys (`unpaid`, `paid`, etc.) as item data, making logic independent of the display language.

## Verification

- Verified all summary cards use localized titles.
- Verified view toggle buttons use localized labels.
- Verified status filter uses localized labels but filters based on internal keys.
- Verified application runs without errors.

## Next Steps

- Ensure other language files (Japanese, Korean, Hindi, Vietnamese) also have the `service` key in `[Invoices]` section if they were not automatically updated (I only updated `en.ini` and `burmese.ini`).
