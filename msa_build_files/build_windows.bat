@echo off
setlocal

echo ======================================
echo MSA Windows Build Script
echo ======================================
echo.

echo [1/6] Cleaning previous build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
echo Done.
echo.

echo [2/6] Checking Python environment...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not found or not in PATH.
    pause
    exit /b 1
)
echo Done.
echo.

echo [3/6] Installing Dependencies...
pip install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo Error installing dependencies.
    pause
    exit /b 1
)
pip install pyinstaller cython --quiet
echo Done.
echo.

echo [4/6] Compiling Security Modules (Cython)...
if exist "build_cython.py" (
    echo Compiling modules...
    python build_cython.py build_ext --inplace
    
    echo Moving compiled modules...
    rem Move compiled .pyd files to source locations for bundling
    rem This moves *any* .pyd matching the names to the right folder
    
    rem license_service
    move /Y license_service*.pyd src\app\services\ >nul 2>&1
    
    rem password_utils
    move /Y password_utils*.pyd src\app\utils\security\ >nul 2>&1
    
    echo Done.
) else (
    echo Warning: build_cython.py not found. Skipping hardening...
)
echo.

echo [5/6] Building Application with PyInstaller...
echo This may take several minutes...
python -m PyInstaller release_win.spec --clean --noconfirm

if %ERRORLEVEL% NEQ 0 (
    echo Build failed!
    pause
    exit /b 1
)
echo.

echo [6/6] Verifying Build...
if exist "dist\MSA\MSA.exe" (
    echo Build Successful!
    echo Application located at: dist\MSA\MSA.exe
) else (
    echo Error: MSA.exe not found in dist output.
    exit /b 1
)
echo.


echo [6/6] Creating Installer with Inno Setup...
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "scripts\msa_installer.iss"
    if %ERRORLEVEL% NEQ 0 (
        echo Installer creation failed!
        pause
    ) else (
        echo Installer created successfully in dist\
    )
) else (
    echo Warning: Inno Setup (ISCC.exe) not found.
    echo Please compile scripts\msa_installer.iss manually or install Inno Setup 6.
)

echo.
echo ======================================
echo Build Complete.
echo ======================================
pause

