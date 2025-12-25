# MSA Lite: Android Deployment Plan

This document outlines the strategy for building **MSA Lite**, a standalone functionality-focused mobile application for solopreneurs.

## 1. Product Vision: "MSA Lite"

A lightweight, offline-first repair shop management app for Android.
**Target Audience:** Freelancers, Solopreneurs, Small Shop Owners.
**Pricing Model:** One-time purchase or low-cost subscription.

### ✅ Core Features (Scope)

1.  **Quick Intake:** Create tickets (Customer + Device + Issue + Price).
2.  **Simple Workflow:** Open -> In Progress -> Ready -> Pickup.
3.  **POS & Receipts:** Generate simple invoices and print to **Bluetooth Thermal Printers**.
4.  **Customer Rolodex:** Simple list with "Click to Call/WhatsApp".
5.  **Mini Dashboard:** Weekly Income + Device Count.

### ❌ Excluded Features (Reduced Bloat)

- Inventory / Stock Management.
- Supplier / Purchase Orders.
- Staff / Roles / Permissions.
- PC Synchronization (This is a standalone app).

---

## 2. Technical Architecture

### A. The Engine

We will reuse the existing **Python (PySide6)** logic but adapted for Android.

- **Language:** Python 3.11 (via PySide6).
- **UI Framework:** PySide6 (QML recommended for mobile smoothness) OR Flet (Flutter-like Python). _Decision Required._ Since we want a "Lite" app, rewriting the UI in **Flet** might be faster and look more "native" than porting the complex Qt desktop widgets.
- **Database:** SQLite (Local storage on phone). `msa_lite.db`.

### B. Directory Structure (Clarification)

**Do we need to move files to the root?**
**No.** We do _not_ need to physically move all files to the root directory just to build the APK.

However, `pyside6-deploy` works best when the entry point is simple.
We should organize the project virtually:

```text
/PyProject/msa/
   ├── src/
   │    ├── app/            <-- Current Desktop Code (Keep as is)
   │    ├── lite/           <-- [NEW] MSA Lite specific code
   │    │    ├── main_lite.py   <-- Entry point for Android
   │    │    ├── ui/            <-- Mobile-specific screens
   │    ├── core/           <-- Shared Logic (Database models, Utils)
```

**Action Item:** We will refactor `src/app/models` and `src/app/utils` into `src/core` so both the Desktop App and the Lite App can import them without duplicating code.

---

## 3. Build & Deployment Steps

1.  **Refactor Core Logic:**

    - Move `models/*.py` to `src/core/models/`.
    - Update Desktop imports to point to `src/core`.

2.  **Develop Lite UI:**

    - Create `src/lite/main_lite.py`.
    - Build the simplified screens (Home, Ticket, Invoice).

3.  **Configure Build:**

    - Run `pyside6-deploy` targeting `src/lite/main_lite.py`.
    - **Permissions:** In `pysidedeploy.spec` and `AndroidManifest.xml`, request:
      - `CAMERA` (QR Scanning)
      - `BLUETOOTH` & `BLUETOOTH_ADMIN` (Thermal Printer)
      - `WRITE_EXTERNAL_STORAGE` (PDF Saving)

4.  **Distribution:**
    - Output: `MSA_Lite_v1.0.apk`
    - Upload to Google Play Console.

## 4. Next Steps

1.  **Code Splitting:** Begin moving `models` strings to a shared `core` folder.
2.  **UI Prototype:** Build the "Home Screen" for MSA Lite using a mobile-first layout.
