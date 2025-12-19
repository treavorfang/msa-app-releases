Step Id: 1137

# Checkpoint 16

# Status: Fixed logic, logging, crashing, PDF/PO generation, refined invoice workflows, localized dialogs, standardized Money Inputs (Live Formatting) and Imports.

## Completed fixes:

1.  **TechnicianRepository**: Renamed `get_by_id` to `get`.
2.  **PartService**: Used `user.id` for logging.
3.  **ModernInvoiceTab**: Fixed safe attribute access.
4.  **TicketReceipt**: Unparented `QPrintDialog`.
5.  **PDF Printing**:
    - **New "Save PDF" Button**: Localized for Burmese.
    - **Crash Prevention**: Use `None` as parent for `QFileDialog`.
    - **Debug Logging**: Added to `handle_save_pdf`.
6.  **PurchaseOrderGenerator**:
    - **Migration**: WeasyPrint HTML/CSS generation.
    - **Localization**: Burmese support.
    - **Bug Fix**: `logo_path` vs `logo_url`.
    - **UX Fix**: Cancel message suppressed.
7.  **Invoice Logic**:
    - **Zero Amount Invoices**: Auto-mark as 'PAID'.
    - **Automation**: Auto-set Labor to 0.00 for Unrepairable/cancelled.
    - **Clarity**: "Waived" description.
    - **Device Status**: Updates `completed_at`.
8.  **PO Item Dialog**:
    - **Localization**: Fully localized.
    - **Formatting**: Currency formatting.
    - **Config**: Added missing `my.ini` keys.
9.  **Standardized Money Input**:
    - **Component**: `MoneyInput` with live `1,000` formatting.
    - **Refactor**: Applied to:
      - `PartDialog`, `AddPOItemDialog`, `CreateInvoiceDialog` (Tax, Discount, Paid, Deposit, Remaining).
      - `RecordCustomerPaymentDialog`, `RecordPaymentDialog`, `BonusManagementDialog`, `ApplyCreditDialog`.
      - `TechniciansTab` (Salary).
      - `TicketReceiptControls` (Estimated Cost, Deposit).
    - **Bug Fix**: Fixed `ModuleNotFoundError` by fixing import paths.

## Next Steps:

- User to verify the application of formatting to all requested fields.
