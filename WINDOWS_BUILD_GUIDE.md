# Windows Build Guide for MSA

This guide explains how to build the MSA application for Windows, including the secure Cython hardening step.

## Prerequisites

1.  **Python 3.10+**: Ensure Python is installed and added to your system PATH.
2.  **Microsoft Visual C++ Build Tools**: Required for compiling Cython modules.
    - Download from: [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
    - Install "Desktop development with C++" workload.

## Setup & Build

1.  **Open Command Prompt (cmd) or PowerShell** as Administrator (recommended).
2.  **Navigate to the project directory**:
    ```cmd
    cd C:\path\to\msa-project
    ```
3.  **Run the Build Script**:
    ```cmd
    build_windows.bat
    ```

## What the Script Does

1.  **Cleans** old `build/` and `dist/` directories.
2.  **Installs Dependencies** from `requirements.txt` (including `Cython` and `PyInstaller`).
3.  **Compiles Sensitive Modules** (`license_service.py`, `password_utils.py`) into efficient C-extensions (`.pyd` files) using your installed C++ compiler.
    - This protects the code from easy reverse-engineering.
4.  **Moves Compiled Modules** to the correct source folders so PyInstaller finds them.
5.  **Builds the Exe** using `release_win.spec`.

## Output

- The built application is found in `dist\MSA\`.
- Run `dist\MSA\MSA.exe` to start the app.
- You can zip the `dist\MSA` folder to distribute it to users.

## Troubleshooting

- **"vcvarsall.bat not found" or C++ errors**: Reinstall Visual C++ Build Tools.
- **"command not found"**: Ensure Python and Scripts are in your PATH.
