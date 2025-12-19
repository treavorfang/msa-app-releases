---
description: Local Network Architecture Plan for MSA Mobile
---

# Local Network Mobile Architecture (MSA)

This plan outlines how to enable Technicians to use a Mobile App (Tablet/Phone) to update job statuses while on the same WiFi network as the main PC, without requiring a public Cloud Server.

## 1. The Concept: "Local Server" Mode

The Main Desktop PC will act as the **Central Server**. All mobile devices on the WiFi will connect directly to this PC's IP address.

```
[Main PC (Server)]  <--- WiFi (192.168.1.10) ---> [Tablet 1 (Technician)]
       |                                                 |
[SQLite DB]                                       [Tablet 2 (Technician)]
```

## 2. Requirements

### A. The Server (Desktop App)

We need to add a "Web API" layer to your existing PySide6 app.

1.  **FastAPI / Flask:** Install a lightweight web framework inside your Python app.
2.  **Multiprocessing:** Run this server in a background thread so it doesn't freeze the GUI.
3.  **Endpoints:** Create JSON API endpoints for the mobile app to hit:
    - `GET /api/tickets` (List assigned jobs)
    - `POST /api/tickets/update_status` (Technician marks "In Progress" or "Done")
    - `POST /api/tickets/add_note`

### B. The Mobile App (Client)

A simple app (or even just a mobile-optimized webpage) that:

1.  **Connects:** Asks the user for the "Server IP" (e.g., `192.168.1.10`).
2.  **Authentication:** Simple PIN code login for technicians.
3.  **UI:** Simple list of "My Jobs". Tap a job -> Update Status.

### C. Network

1.  **Static IP:** The Main PC ideally needs a Static Local IP (so it doesn't change from `.10` to `.12` randomly).
2.  **Firewall:** Windows Firewall must allow port `8000` (or similar) to accept incoming connections.

## 3. Detailed Implementation Roadmap

### Phase 1: Server Core Infrastructure (The Background Engine)

**Goal:** Enable the Desktop App to listen for HTTP requests in the background.

1.  **Dependency Setup**

    - Add `fastapi`, `uvicorn`, `python-multipart` to `requirements.txt`.
    - Verify `src/app/api` exists.

2.  **The API Worker (`src/app/api/worker.py`)**

    - Create `ServerWorker` class passing `QThread`.
    - Implement `run()` method to start Uvicorn programmatically (`uvicorn.run(app, host="0.0.0.0", port=8000)`).
    - Add `stop()` signal to safely shut down the server when the Desktop App closes.

3.  **The Application Hook (`src/app/main.py`)**
    - Import `ServerWorker`.
    - In `main()`, instantiate `input_server = ServerWorker()`.
    - Add a configuration check: `if flags.ENABLE_MOBILE_SERVER: input_server.start()`.

### Phase 2: Database Safety Layer (Crucial)

**Goal:** Prevent "Database Locked" errors when both Phone and PC write at the same time.

1.  **WAL Mode Activation**
    - In `src/app/config/database.py`, modify the connection string or initialization:
      ```python
      db.connect()
      db.execute_sql("PRAGMA journal_mode=WAL;")
      db.execute_sql("PRAGMA synchronous=NORMAL;")
      ```
    - Verify WAL file (`msa.db-wal`) appears on disk.

### Phase 3: Mobile Functionality & Endpoints

**Goal:** Define what the phone can actually _do_. We will create these API routes in `src/app/api/routes.py`.

#### Feature A: Technician Dashboard ("My Jobs")

- **Endpoint:** `GET /api/tickets/assigned/{tech_id}`
- **Response:** JSON list of tickets `[{id: 101, device: "iPhone 13", status: "In Progress"}]`.
- **Mobile UI:** A clean list view. Tapping a card opens details.

#### Feature B: Quick Status Update

- **Endpoint:** `POST /api/tickets/{ticket_id}/status`
- **Payload:** `{ "status": "Ready for Pickup", "note": "Fixed screen." }`
- **Action:** Updates the SQLite record immediately.
- **Desktop Notification:** Emit a PyQt Signal so the Desktop User sees a popup: _"Tech A updated Ticket #101"_.

#### Feature C: Photo Upload (Camera Integration)

- **Endpoint:** `POST /api/tickets/{ticket_id}/upload`
- **Action:** Accepts form-data (image). Saves file to `User_Data/Ticket_Photos/{id}/`.
- **Mobile UI:** A big camera button. Uses HTML5 `<input type="file" capture="environment">`.

#### Feature D: Customer Signature (Tablets)

- **Mobile UI:** HTML5 Canvas element for drawing signature.
- **Endpoint:** `POST /api/tickets/{ticket_id}/sign`
- **Action:** Saves signature as PNG. Adds to PDF Invoice.

### Phase 4: The Mobile "App" (HTML Frontend)

**Goal:** Create the interface using our new "Modern Dark Theme".

1.  **Structure (`src/app/ui_mobile/`)**

    - `index.html`: Login / Home (Tech vs Customer modes).
    - `tech_dashboard.html`: List of jobs.
    - `ticket_detail.html`: Status toggle, Notes, Camera.
    - `intake_form.html`: For creating new customers + Signature.
    - `css/style.css`: The "Nano Banana" dark theme CSS.

2.  **Serving the UI**
    - In `src/app/api/main.py`: `app.mount("/static", StaticFiles(directory="ui_mobile"), name="static")`.
    - Redirect root `/` to `/static/index.html`.

### Phase 5: Security & Pairing

**Goal:** Prevent random people on WiFi from accessing data.

1.  **Simple Auth Token**

    - Desktop App generates a daily 4-digit PIN (e.g., "Shop PIN: 4829").
    - Mobile User must enter "4829" to login.
    - FastAPI Middleware checks headers for this PIN.

2.  **QR Code Pairing**
    - Desktop App shows a QR Code containing: `http://192.168.1.15:8000?pin=4829`.
    - Technician scans it -> Instantly logged in.

## 4. Hardware Requirements

- **Main PC:** Must be connected via Ethernet (preferred) or Stable WiFi.
- **Router:** Standard Router is fine. Firewalls must allow **Port 8000**.
- **Mobile:** Any Smartphone/Tablet with a browser (Chrome/Safari). 5+ years old is fine. It just renders HTML.

## 4. Pros & Cons

| Feature           | Local Network Mode        | Cloud (Firebase) Mode         |
| :---------------- | :------------------------ | :---------------------------- |
| **Privacy**       | 100% Data stays in shop   | Data stored on Google Servers |
| **Cost**          | Free                      | Free tier, then paid          |
| **Setup**         | Harder (Firewall, IP IPs) | Easier (Just login)           |
| **Remote Access** | None (Must be in shop)    | Work from anywhere            |
| **Speed**         | Instant                   | Depends on internet           |

## Recommendation

For a shop management system, **Local Network Mode with a Browser Interface** is best.

1.  Technicians just open a link. No app store installation.
2.  Zero monthly cloud costs.
3.  Fastest update speed.
