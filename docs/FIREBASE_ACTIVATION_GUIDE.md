# Firebase Activation Method

**Firebase** (by Google) is a popular "Backend-as-a-Service" that makes implementing **Online Activation** much easier than building your own server.

## How it works (The Flow)

Instead of a License Key, the user logs in with their Google Account.

1.  **Login:** User opens app -> Clicks "Login with Google".
2.  **Auth:** Firebase handles the secure login popup (OAuth).
3.  **Verification:**
    - App connects to **Firebase Firestore** (Cloud Database).
    - App looks for a document in the `licenses` collection matching the user's email.
    - _Query:_ `db.collection('licenses').doc('user@gmail.com').get()`
4.  **Decision:**
    - **Found Check:** Does the document exist?
    - **Expiry Check:** Is `expires_at > today`?
    - **HWID Check:** Does `hardware_id` match current computer? (Prevents account sharing).
5.  **Unlock:** If all checks pass, the app opens.

## Pros & Cons compared to Offline Keys

| Feature             | Offline Keys (Current)             | Firebase (Online)                            |
| :------------------ | :--------------------------------- | :------------------------------------------- |
| **Logic Location**  | User's Computer (Verified by Math) | Google's Cloud (Verified by Server)          |
| **Internet**        | **Not Needed**                     | **Required** for Login (and periodic checks) |
| **User Experience** | Copy/Paste Key code                | "Sign in with Google" button (Slick)         |
| **Control**         | Hard to revoke                     | **Revoke instantly** (Delete doc from DB)    |
| **Cost**            | Free (Zero cost)                   | Free (Generous tier) -> Paid if huge         |
| **Difficulty**      | Medium (Cryptography)              | Medium (Async Web Requests)                  |

## Implementation Roadmap (If you want to switch)

1.  **Setup:** Create a Project at `console.firebase.google.com`.
2.  **Dependencies:** Install `firebase-admin` (for you) and `pyrebase4` or requests (for the app).
3.  **Store:**
    - You manually create a record in Firestore for each customer.
    - Structure: `licenses/user@gmail.com = { "valid": true, "hwid": "..." }`
4.  **App Code:**
    - Replace `LicenseDialog` with a `LoginDialog`.
    - Implement the API call to check Firestore on startup.

## Recommendation

**Firebase is excellent** if you prioritize _Control_ (banning users, monthly subscriptions) and _UX_ (Google Login).
**Offline Keys are excellent** if you prioritize _Simplicity_ and _Offline reliability_ (users can use the app in a basement with no wifi).

For a desktop business app like MSA (Mobile Service Accounting), **Offline Keys** are traditionally preferred because shop owners might have unstable internet or want to "own" the software forever.
