---
description: Hybrid HTML/Python UI Migration Plan
---

# Hybrid UI Migration Plan (MSA 2.0)

This plan outlines the steps to gradually migrate the MSA application from a pure PySide6 Widgets UI to a Hybrid Architecture (PySide6 Backend + HTML/CSS Frontend).

## 1. Preparation

- [ ] Add `PySide6-WebEngine` to `requirements.txt`.
- [ ] Create a standard `ui/` directory structure for web assets:
  ```
  src/app/ui/
  ├── components/    # Reusable HTML widgets (Cards, Buttons)
  ├── pages/        # Full page templates (Login, Dashboard)
  ├── assets/       # CSS, JS, Images, Fonts
  └── bridge.js     # Standard QWebChannel connector
  ```

## 2. Phase 1: The Login Screen (Pilot)

- [ ] Port `ui_experiments/login_theme.html` to `src/app/ui/pages/login.html`.
- [ ] Modify `src/app/views/auth/login.py` to use `QWebEngineView`.
- [ ] Implement the `LoginBridge` python class to handle:
  - `tryLogin(email, password)`
  - `closeWindow()`
  - `minimizeWindow()`
- [ ] Verify keyboard focus and tab navigation works (common WebEngine gotcha).

## 3. Phase 2: The Core Dashboard

- [ ] Migrate the Main Dashboard to HTML to utilize Chart.js.
- [ ] Create a `DashboardBridge` to pass data from Python to JS:
  - Methods: `update_metrics()`, `refresh_charts()`
- [ ] Ensure the "Native" menu bar or sidebar still controls navigation (or move nav to HTML).

## 4. Phase 3: Printing & Hardware

- [ ] Keep `invoice_generator.py` logic in Python (Backend).
- [ ] Create a UI in HTML for "Print Preview".
- [ ] Use the Bridge to trigger the actual print job: `bridge.printInvoice(invoice_id)`.

## 5. Deployment

- [ ] Update `.spec` files (PyInstaller) to include the `src/app/ui` folder as datas.
- [ ] Verify app size constraints.

## Risks & Mitigations

- **Memory Usage:** Monitor RAM usage. If >500MB, optimize the number of WebEngine instances (use a single SPA instance).
- **Startup Speed:** Show a splash screen while the WebEngine initializes.
