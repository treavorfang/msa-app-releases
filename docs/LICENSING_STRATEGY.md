# Licensing Strategy for MSA

## Overview

To commercialize and sell the MSA application securely, a licensing system prevents unauthorized usage and casual piracy.

## Recommended Licensing Models

### 1. Node-Locked Perpetual License (Recommended)

**How it works:**  
The license key is mathematically tied to the user's specific computer hardware (CPU, Motherboard, etc.).

- **Pros:** Prevents a single key from being used on 100 computers. High security.
- **Cons:** If the user buys a new PC, they need a license transfer (support ticket).
- **Security:** High (Asymmetric Key Cryptography).

### 2. Time-Based Subscription (SaaS)

**How it works:**  
The application checks a "valid until" date secure inside the license key.

- **Pros:** Recurring revenue model (e.g., $29/month).
- **Cons:** App stops working if they stop paying.
- **Security:** High (if key is signed).

### 3. Simple Serial Key (Legacy)

**How it works:**  
A simple code (e.g., `MSA-1234-ABCD`) verified by an algorithm.

- **Pros:** Easy to implement, easy for users.
- **Cons:** Extremely insecure. One key can be shared on the internet for everyone.

---

## Technical Implementation: The "Secure Hybrid" Approach

We will implement **Option 1 (Node-Locked)** using **Asymmetric Cryptography**.

### The Flow

1.  **Fingerprint:** The App generates a unique `Machine ID` (Hardware Fingerprint) based on CPU/Disk Serial.
2.  **Purchase:** The User sends you this `Machine ID` (e.g., on your checkout page).
3.  **Generation:** You (the admin) use a private tool to generate a **License Key**.
    - The key contains: `Machine ID`, `Expiry Date`, `Feature Flags`.
    - The key is **Signed** with your **Private Key**.
4.  **Activation:** User enters the License Key in the App.
5.  **Verification:** The App uses the embedded **Public Key** to verify the signature.
    - If signature is valid AND `Machine ID` matches -> **App Opens**.

### Required Library

We need the `cryptography` python library for robust security (RSA or Ed25519 signing).
`pip install cryptography`

## Next Steps

1.  Add `cryptography` to requirements.
2.  Create `LicenseService` to generate Machine IDs.
3.  Create an Admin Script (`scripts/generate_license.py`) for YOU to generate keys.
4.  Create a "License Activation Dialog" in the app that blocks access if unlicensed.
