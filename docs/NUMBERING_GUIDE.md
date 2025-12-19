# Document Numbering Guide

This guide explains how to customize the numbering formats for your tickets, invoices, and purchase orders.

## How to Customize

Navigate to **Settings** -> **Customization** to define your preferred numbering patterns.

## Placeholder System

The system uses "placeholders" (text inside `{ }`) that are automatically replaced with real data when a document is generated.

| Placeholder | Description                          | Example Output          |
| :---------- | :----------------------------------- | :---------------------- |
| `{branch}`  | The ID of the current branch.        | `1`, `2`, `5`           |
| `{date}`    | The current date in `YYMMDD` format. | `231219` (Dec 19, 2023) |
| `{seq}`     | A 4-digit auto-incrementing number.  | `0001`, `0042`, `1024`  |

---

## Example Formats

### 1. Default Pattern

**Format**: `INV-{branch}{date}-{seq}`  
**Result**: `INV-1231219-0001`  
_Best for: Standard organized tracking._

### 2. Simple Serial

**Format**: `TKT-{seq}`  
**Result**: `TKT-0001`  
_Best for: Shops that don't need date or branch info in the number._

### 3. Shop Specific

**Format**: `MYSHOP-{date}{branch}-{seq}`  
**Result**: `MYSHOP-2312191-0001`  
_Best for: Branding your document numbers._

---

## ⚠️ Important Rules

1. **Uniqueness**: Ensure your format includes `{seq}` to keep numbers unique.
2. **Length**: Keep your formats reasonable in length (under 30 characters total) to ensure they print correctly on small receipts.
3. **Sequence**: The sequence number `{seq}` automatically starts at `0001` for the first document and resets or continues based on your shop's database.
