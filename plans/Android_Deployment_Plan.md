# Android Deployment Plan for MSA

This document outlines the steps to port the existing PySide6 (Qt) application (MSA) to Android.

## 1. Prerequisites

To build for Android, you need a development environment set up with:

- **Java Development Kit (JDK)**: Version 11 or 17 recommended.
- **Android SDK Only (via command line)** or **Android Studio** (for SDK manager and emulator).
- **Android NDK**: Required for compiling Python C-extensions (like `cryptography`, `peewee`).

## 2. Tools

We will use **PySide6's Deployment Tool** (`pyside6-deploy`).
This tool automates the process of:

1.  Packaging your Python code.
2.  Downloading a pre-built Qt implementation for Android.
3.  Generating an Android APK/AAB.

## 3. Deployment Steps

### Step 1: Install Deployment Tools

Install `pyside6-deploy` in your development environment:

```bash
pip install pyside6-deploy
```

### Step 2: Generate Deployment Configuration

Run the deploy tool in the root directory of your project (where `src` is accessible):

```bash
pyside6-deploy
```

This interactive command will ask you to:

- Name the application (MSA).
- Point to the entry point (`src/app/main.py`).
- Select the `requirements.txt` file.

It will generate a `pysidedeploy.spec` file. You can commit this file to your repository.

### Step 3: Configure Dependencies (`pysidedeploy.spec`)

Open `pysidedeploy.spec` and ensure:

- `requirements` list includes `peewee`, `reportlab`, `cryptography`, etc.
- **Windows-only dependencies** like `pywin32` or `psutil` (platform conditional) must be **excluded** or handled carefully. The build process runs on your host (Mac/Windows), but compiles for Android. `pywin32` will definitely break the build if included for Android.
- Ensure `modules` list includes essential Qt modules used (`QtWidgets`, `QtSql`, `QtGui`, `QtCore`).

### Step 4: Handle Local Files

Android apps are packaged as zipped assets.

- If your app writes files (LOGS, DATABASE), you **cannot** write to the application folder.
- You typically need to use `QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)` to find a writable path on Android.
- Verify `src/app/config/flags.py` logic for `get_db_path` uses standard paths or environment variables that work on Android.

### Step 5: Build the APK

Run the deploy command again to build:

```bash
pyside6-deploy
```

If successful, this will produce an `.apk` file in the build directory.

## 4. Code Adjustments Required

1.  **UI Layout**: The current `MainWindow` is likely designed for desktop dimensions (1024x768+). On a phone, this will be unusable.
    - **Strategy**: Implement a `MobileMainWindow` or use `QScroller` areas to allow panning.
    - **Response**: Mobile interfaces use different patterns (Stack navigation vs Tab navigation). You might need a simplified UI for mobile.
2.  **Permissions**: Android requires explicit permissions (Camera, Internet, Storage) in `AndroidManifest.xml` (which the deploy tool can help generate/modify).
    - Camera is needed for QR code scanning.
3.  **File System**: Ensure no absolute paths (like `C:/` or `/Users/`) are hardcoded.

## 6. Architectural Considerations (Future Refactoring)

When you are ready to begin development on the mobile app (`msa_mobile`), you will likely need to restructure the project to share logic between the Desktop and Mobile applications.

### A. The "Shared Core" Strategy

To avoid writing business logic twice, the project should eventually be refactored into:

```text
/PyProject/msa/
   ├── src/
   │    ├── core/           <-- Shared logic (Models, Controllers, Database, Services)
   │    ├── app/            <-- Current Desktop UI (PySide6 Desktop)
   │    └── msa_mobile/     <-- Future Mobile UI (PySide6 Mobile / Flet)
```

**Impact Warning**: Moving `models` and `services` to `core` will break imports in the current Desktop app. This refactoring should be treated as a major maintenance task (1-2 days of work) and done only when active development on the Mobile app begins.

### B. The Database Challenge

The current application uses a local SQLite database file on the computer's hard drive.

- **Problem**: A mobile app running on a phone will have its own isolated file system and cannot access the computer's `.db` file directly.
- **Solutions**:
  1.  **Cloud Database (Recommended)**: Migrate from SQLite to a cloud-hosted PostgreSQL/MySQL database. Both Desktop and Mobile apps connect to this central server.
  2.  **API Server**: The Desktop app runs a local web server, and the Mobile app communicates with it over Wi-Fi.
  3.  **Synchronization**: Complex logic to sync two separate SQLite databases when the devices are near each other.

## 7. Alternative: BeeWare (Briefcase)

If PySide6 deployment proves too difficult due to C-extension compatibility, **BeeWare** is an alternative.

- Uses `briefcase` to wrap the app.
- Might require more configuration for complex dependencies.

## 8. Alternative: Kivy/Flet (Rewrite)

If the UI is too "desktop-heavy", rewriting the frontend in **Kivy** or **Flet** (Flutter for Python) is a cleaner but more expensive option. Flet is particularly good for creating modern mobile interfaces quickly in Python.

## Recommendation

**Current Status**: Deferred.

**Action Plan when starting Mobile Dev**:

1.  **Refactor**: Create `src/core` and move shared logic (Models, Services, Utils) there. Update all Desktop app imports.
2.  **Database Strategy**: Decide if the mobile app needs real-time data (requires Cloud DB) or can work offline (requires Sync).
3.  **Prototype**: Build a "Hello World" PySide6 Android app to verify the build pipeline before migrating the full MSA codebase.
