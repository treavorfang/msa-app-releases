# Activation System Refinement Plan

## Objective

Refine the activation process to separate concerns, improve data tracking, and implement a robust audit trail. We will restructure the Firebase database and update both the MSA App (Client) and License Generator (Admin) to support this new schema.

## 1. Firebase Database Restructuring

We will split the single data table into three distinct collections to handle customer profiles, financial records, and security logs separately.

### A. `customers` Collection

_Stores user profile and current license status. The "Source of Truth" for access._

**Schema:**

```json
{
  "id": "email_hash_or_uid",
  "email": "user@example.com",
  "profile": {
    "name": "John Doe",
    "phone": "+959...",
    "city": "Yangon",
    "country": "Myanmar"
  },
  "license": {
    "status": "active", // active, pending, suspended, expired
    "type": "gold", // subscription tier
    "hwid": "MAC-ADDRESS-...", // Hardware Lock
    "expiry_date": "2025-12-31",
    "last_check_in": "2024-12-15T10:00:00Z"
  },
  "created_at": "timestamp"
}
```

### B. `invoices` Collection

_Stores financial history, subscriptions, and purchase records._

**Schema:**

```json
{
  "id": "INV-2024-1215-001",
  "customer_id": "link_to_customer_doc_id",
  "amount_details": {
    "currency": "MMK",
    "amount": 200000,
    "discount": 0,
    "total": 200000
  },
  "payment": {
    "method": "KBZPay", // KBZPay, Cash, Bank Transfer
    "status": "paid", // paid, pending, void
    "date": "timestamp"
  },
  "items": [{ "name": "1 Year Subscription", "duration_days": 365 }],
  "notes": "Special discount for early bird"
}
```

### C. `audit_logs` Collection

_Immutable history of login attempts, activations, and security events._

**Schema:**

```json
{
  "id": "auto_generated",
  "customer_id": "link_to_customer_doc_id",
  "event_type": "login", // login, activation, renewal_update, failed_attempt
  "status": "success",
  "details": {
    "hwid": "MAC-...",
    "ip_address": "192.168.1.1",
    "app_version": "1.0.2",
    "message": "Login successful"
  },
  "timestamp": "server_timestamp"
}
```

---

## 2. Implementation Steps

### Phase 1: License Generator (Admin Tool) Updates

The License Generator is the "Writer" of this data. It needs to handle the complexity of approving users and generating invoices.

- **Update `online_manager.py`**:

  - Add methods to write to `customers` (update profile/license).
  - Add methods to create `invoices`.
  - Remove legacy monolithic "user" update logic.

- **Update `OnlineAdminView` UI**:
  - **Pending Requests**: When creating a license for a "Pending" user:
    - Pull data from the Registration request.
    - Allow Admin to fill in **Invoice Details** (Currency, Amount, Method).
    - On "Activate":
      1.  Update `customers` -> `status: active`, `expiry_date`, `hwid`.
      2.  Create `invoices` record.
      3.  (Optional) Send confirmation email.
  - **Customer Dashboard**:
    - View full history of Invoices for a selected customer.
    - View Audit Logs (See when they last logged in).

### Phase 2: MSA App (Client) Updates

The MSA App is the "Reader" and "Reporter". It needs to authenticate lightly but log heavily.

- **Update `LicenseService` (`src/app/services/license_service.py`)**:
  - **Login Flow**:
    - Authenticate user (Email/Password).
    - Fetch `customers/{id}/license`.
    - **Validation**: Check `status == active` AND `expiry_date > today` AND `hwid == current_machine`.
  - **Audit Logging**:
    - On every **successful login**, write to `audit_logs` (Update `last_login` timestamp).
    - On **failed login** (wrong HWID), write a "Security Alert" to `audit_logs`.
  - **State Management**:
    - Store `renew_remainder` locally to warn user if expiry is close.

### Phase 3: Data Migration (If needed)

- Create a script `tools/license_generator/migrate_structure.py` to move existing `users` data into the new `customers` and `invoices` format.

## 3. Summary of Code Changes Required

| Component     | File                                  | Action                                                                       |
| :------------ | :------------------------------------ | :--------------------------------------------------------------------------- |
| **Generator** | `tools/.../core/online_manager.py`    | Add `create_invoice`, `log_audit`, `approve_customer` functions.             |
| **Generator** | `tools/.../ui/online_admin_view.py`   | Add UI for Invoice entry during activation. Show Audit Logs.                 |
| **MSA App**   | `src/app/services/license_service.py` | Update `check_online_status` to respect new schema. Add `log_activity` call. |
| **MSA App**   | `src/app/views/auth/login.py`         | Ensure login flow triggers the service's audit logging.                      |
