@echo off
SETLOCAL EnableDelayedExpansion

echo ==========================================
echo      MSA Windows Build Script
echo ==========================================
echo.

:: Step 1: Clean previous build artifacts
echo Step 1: Cleaning previous build artifacts...
if exist "build" (
    echo Removing build directory...
    rmdir /s /q build
)
if exist "dist" (
    echo Removing dist directory...
    rmdir /s /q dist
)
echo [OK] Cleaned build directories
echo.

:: Step 2: Check Python installation
echo Step 2: Checking Python environment...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Found Python %PYTHON_VERSION%
echo.

:: Step 2.5: Setup Virtual Environment
echo Step 2.5: Setting up virtual environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo [OK] Virtual environment active
echo.

:: Step 3: Check/Install PyInstaller
echo Step 3: Checking/Installing PyInstaller...
python -m pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
) else (
    for /f "tokens=2" %%i in ('python -m pip show pyinstaller ^| findstr Version') do set PYINSTALLER_VERSION=%%i
    echo [OK] PyInstaller !PYINSTALLER_VERSION! is installed
)
echo.

:: Step 4: Verify dependencies
echo Step 4: Verifying dependencies...
echo Installing/Updating dependencies...
python -m pip install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies verified
echo.

:: Step 5: Check icon file
echo Step 5: Checking icon file...
if exist "src\app\static\icons\logo.png" (
    echo [OK] Icon file found
) else (
    echo [WARNING] Icon file not found, build will continue without icon
)
echo.

:: Step 6: Update version information (optional)
echo Step 6: Updating version information...
if exist "scripts\generate_version.py" (
    python scripts\generate_version.py
    echo [OK] Version updated
) else (
    echo [WARNING] Version update script not found, skipping...
)
echo.

:: Step 7: Build application with PyInstaller
echo Step 7: Building application with PyInstaller...
echo This may take several minutes...
echo.
pyinstaller release.spec --noconfirm --clean

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ==========================================
    echo [ERROR] Build Failed!
    echo ==========================================
    echo.
    echo Check the error messages above for details.
    pause
    exit /b 1
)

echo [OK] Build completed successfully
echo.

:: Step 8: Verify build output
echo Step 8: Verifying build output...
if exist "dist\MSA\MSA.exe" (
    for %%A in ("dist\MSA") do set SIZE=%%~zA
    set /a SIZE_MB=!SIZE! / 1048576
    echo [OK] Application created: !SIZE_MB! MB
) else (
    echo [ERROR] Build output not found!
    pause
    exit /b 1
)
echo.

:: Step 9: Create installer (optional - requires Inno Setup)
echo Step 9: Creating installer (optional)...
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    if exist "installer\windows_installer.iss" (
        echo Creating installer with Inno Setup...
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\windows_installer.iss
        if %ERRORLEVEL% EQ 0 (
            echo [OK] Installer created
        ) else (
            echo [WARNING] Installer creation failed
        )
    ) else (
        echo [INFO] Installer script not found, skipping...
    )
) else (
    echo [INFO] Inno Setup not installed, skipping installer creation...
    echo       Install from: https://jrsoftware.org/isdl.php
)
echo.

echo ==========================================
echo Build Complete!
echo ==========================================
echo.
echo Build artifacts:
echo   * Application: dist\MSA\MSA.exe
echo   * All files:   dist\MSA\
echo.
echo To test the application:
echo   dist\MSA\MSA.exe
echo.
echo To distribute:
echo   1. Zip the entire dist\MSA\ folder, or
echo   2. Use the installer (if created)
echo.
echo Note: For distribution, you may want to:
echo   1. Sign the executable with a code signing certificate
echo   2. Create an installer with Inno Setup or NSIS
echo   3. Test on a clean Windows machine
echo ==========================================
echo.

pause
