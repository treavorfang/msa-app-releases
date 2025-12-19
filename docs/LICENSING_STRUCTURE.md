# MSA Licensing Structure Overview

This document maps out the files that make up the security system for the Mobile Service Accounting (MSA) application.

## 🏆 The "Most Important" File: `private.pem`

- **Location:** Project Root (Currently `/Users/studiotai/PyProject/msa/private.pem`)
- **Role:** The **Master Key**. It is used to digitally sign user licenses.
- **Security Risk:** 🔴 **CRITICAL**.
- **Action:** **NEVER share this file.** Do not include it in the built app. Keep it safe on your personal computer or a secure USB drive. If a hacker gets this, they can create a "Key Generator" and give everyone free licenses.

---

## 📂 File Locations & Roles

### 1. The Secrets (Developer Only)

These files stay on your computer.

| File                    | Location                    | Role                                                                                          |
| :---------------------- | :-------------------------- | :-------------------------------------------------------------------------------------------- |
| **`private.pem`**       | `Root / private.pem`        | **Signs Licenses.** The only file that can make a valid key.                                  |
| **`generate_keys.py`**  | `scripts/generate_keys.py`  | **One-time Setup.** Created the public/private pair. You likely won't need to run this again. |
| **`create_license.py`** | `scripts/create_license.py` | **The Admin Tool.** You run this when you make a sale to generate a key for a customer.       |

### 2. The Locks (Shipped with App)

These files are included in the final software (`.exe` / `.app`) sent to users.

| File                     | Location                    | Role                                                                                                                            |
| :----------------------- | :-------------------------- | :------------------------------------------------------------------------------------------------------------------------------ |
| **`public.pem`**         | `src/app/config/public.pem` | **The Verifier.** Allows the app to check if a license is authentic. It _cannot_ generte new licenses. It is safe to be public. |
| **`license_service.py`** | `src/app/services/`         | **The Logic.** Code that reads the key, calculates the Hardware ID, and runs the verification check.                            |
| **`license_dialog.py`**  | `src/app/views/dialogs/`    | **The UI.** The popup window asking for the key if one is missing.                                                              |

### 3. The User's Key (On Their Computer)

This file is created on the customer's machine after activation.

| File              | Location             | Role                                                                                   |
| :---------------- | :------------------- | :------------------------------------------------------------------------------------- |
| **`license.key`** | `Root / license.key` | **The Ticket.** Contains the encrypted string (Machine ID + Expiry) proving they paid. |

---

## 🔄 How it Works Together

1.  **You** hold the `private.pem`.
2.  **Customer** sends you their Machine ID.
3.  **You** use `create_license.py` + `private.pem` to create a `license.key`.
4.  **Customer** puts `license.key` in their app.
5.  **The App** uses `public.pem` to confirm `license.key` was signed by you.
6.  **The App** unlocks.
