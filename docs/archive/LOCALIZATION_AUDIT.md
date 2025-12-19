# Localization Audit

**Date**: 2025-12-06
**Scope**: All UI Components

## 🔴 Critical Issues

### 1. Hardcoded Strings in `restock_dialog.py`

This file has no localization at all.

- Window title: "Restock Part - {name}"
- Group Boxes: "Part Information", "Restock Options"
- Labels: "SKU:", "Name:", "Brand:", "Current Stock:", "Min Stock Level:", "Quantity:"
- Radio Buttons: "Add to stock", "Set stock to", "Remove from stock"
- Buttons: "Cancel", "Update Stock"
- Messages: "Invalid Quantity", "Insufficient Stock", "Confirm Stock Update", "Success", "Error"

### 2. Hardcoded Strings in `part_dialog.py`

Partial localization, but some missing:

- Placeholders: "Enter brand", "e.g., iPhone 12...", "Enter part name"
- Labels: "Brand:", "Compatible Models:", "Status:"
- Hints: "Auto-format..." (Maybe okay to keep English as technical spec?)
- Validation errors: "Part name is required", "Category is required", etc.

### 3. Hardcoded Strings in `record_customer_payment_dialog.py`

Need to check this file.

### 4. Hardcoded Strings in `ticket_receipt.py`

- "Lock Type:", "PIN", "Pattern", "Face ID", "Fingerprint" (Some are technical terms, but "Lock Type" should be localized)
- "Accessories Received:"
- "Other"

## 🟡 Potential Issues

### 1. English-only error messages in Logic

Many `try...except` blocks hardcode error strings like "Failed to update stock: {str(e)}".

### 2. Date Formats

Ensure dates are formatted according to locale or user preference, not just `strftime`.

## 📝 Plan

1.  **Fix `restock_dialog.py`** - Complete localization.
2.  **Fix `part_dialog.py`** - Add missing translations.
3.  **Audit & Fix `record_customer_payment_dialog.py`**.
4.  **Audit & Fix `ticket_receipt.py`** (remaining items).
5.  **Scan other views** for similar patterns.
