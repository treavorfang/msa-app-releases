# Firebase Cloud Functions for MSA Authentication

This document outlines the backend logic required to support your new MSA "Always Online" authentication system.

You can implement these functions using **Node.js (TypeScript/JavaScript)** or **Python** depending on your Firebase setup.

## 1. Data Structure (Firestore)

Create a collection named `users` (or `licenses`).

**Document ID**: `email` (or a unique UUID)

**Fields**:

- `email` (string)
- `password_hash` (string) - _Securely hashed!_
- `hwid` (string) - _The Machine ID locked to this account_
- `status` (string) - `active`, `pending`, `suspended`
- `expiry_date` (timestamp)
- `name` (string)

---

## 2. API Endpoints

### A. `/login_lock_check` (POST)

**Purpose**: Authenticate user AND verify they are on the correct machine.

**Input**:

```json
{
  "email": "user@example.com",
  "password": "plain_password",
  "hwid": "ABCD-1234-EFGH-5678"
}
```

**Logic**:

1.  Fetch user document from Firestore by `email`.
2.  **Verify Password**: content match? (Use bcrypt/argon2).
3.  **Check HWID**:
    - IF `doc.hwid` matches `input.hwid`: **PASS**
    - IF `doc.hwid` is EMPTY (First login): Update `doc.hwid` = `input.hwid`. **PASS (Bind)**
    - IF `doc.hwid` does NOT match: **FAIL** (Return 403 "Device Mismatch").
4.  **Check Status**:
    - IF `status` == 'pending': Return `{"status": "pending"}`.
    - IF `status` == 'active': Return `{"status": "active", "token": "generated_jwt_or_session_key", "expiry": "..."}`.

**Response (Success)**:

```json
{
  "status": "active",
  "valid": true,
  "name": "John Doe",
  "expiry": "2025-12-31"
}
```

---

### B. `/register_device` (POST)

**Purpose**: Create a new account in "Pending" state.

**Input**:

```json
{
  "email": "new@example.com",
  "password": "plain_password",
  "hwid": "ABCD-1234-EFGH-5678"
}
```

**Logic**:

1.  Check if `email` already exists. If yes, return Error.
2.  Create new document in `users`:
    - `email`: input.email
    - `password`: hash(input.password)
    - `hwid`: input.hwid
    - `status`: "pending"
    - `created_at`: server_timestamp
3.  Return Success.

---

### C. `/check_license` (POST)

**Purpose**: Passive check on app startup (Auto-Login).

**Input**:

```json
{
  "license_key": "jwt_token_or_session_id",
  "hwid": "ABCD-1234-EFGH-5678"
}
```

_Note: In our client implementation, we saved the 'token' into the license.key file._

**Logic**:

1.  Verify the token.
2.  Check if the associated user is still `active` and `hwid` matches.
3.  Return Status.

---

## 3. Deployment

1.  Set up Firebase CLI (`npm install -g firebase-tools`).
2.  `firebase init functions`.
3.  Write the logic in `functions/index.js` (or `.py`).
4.  `firebase deploy --only functions`.
5.  Copy the resulting URL (e.g., `https://us-central1-...`) into `src/app/services/license_service.py`.
