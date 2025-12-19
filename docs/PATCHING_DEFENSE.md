# Deep Dive: What is "Patching"?

**Patching** is when a hacker modifies your application's executable file (`MSA.exe` or `MSA.app`) to bypass security checks.

## How it works (The Attack)

1.  **Decompilation:** The hacker turns your compiled app back into readable code.
2.  **Search:** They search for keywords like `license`, `valid`, `check`, `register`.
3.  **Modification:**
    - They find: `if license.is_valid(): open_app()`
    - They change it to: `if True: open_app()`
4.  **Re-compilation:** They build a new `.exe` and distribute it.

## Defense Strategy: "The Hydra" (Distributed Checks)

If you only have **one** guard at the front door (the check in `main.py`), the hacker only needs to kill one guard.
To defend against patching, you must put guards **everywhere**.

### 1. Distributed License Checks

Don't just check at startup. Check inside critical business functions.

- **Startup:** Check License.
- **Save Ticket:** Check License again.
- **Print Invoice:** Check License again.
- **View Report:** Check License again.

**Why this works:** The hacker patches the startup check and thinks they won. Then they try to save a ticket, and it fails. They have to find _that_ check too. If you hide 50 checks, they usually give up because it's too much work.

### 2. Silent Failures (Frustration)

Don't show an error message like "License Invalid" (which helps them find the code).
Instead, just make the app **misbehave**.

- If license check fails during "Print Invoice":
  - _Bad:_ Show popup "Error: No License". (Hacker searches for this string).
  - _Good:_ Generate the PDF but make all the text blurry or incorrect.
- If license check fails during "Save Ticket":
  - _Good:_ Save the ticket, but randomly corrupt the customer name.

This makes the "Cracked" version useless, and users will complain to the hacker that the crack is "buggy".

### 3. Integrity Checks (Checksums)

The app calculates a "Hash" (fingerprint) of its own code files on startup.

- If `hash(file) != expected_hash`: The file has been modified (patched).
- **Action:** Crash immediately.

## Implementation Plan

1.  **Modify Services:** Add `check_license()` calls inside `TicketService` and `InvoiceService`.
2.  **Obfuscate Strings:** Don't use the string "License" in your code. Use generic names like `verify_system_integrity()` or `check_config()`.
