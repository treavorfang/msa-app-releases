@echo off
setlocal

echo ======================================
echo MSA Windows Build Script
echo ======================================
echo.

if "%~1"=="__run__" goto :LogProcess

echo Logging output to build_log.txt...
powershell -Command "& {cmd /c '%~f0' __run__} | Tee-Object -FilePath 'build_log.txt'"
exit /b

:LogProcess

echo [1/6] Archiving and cleaning previous build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" (
    if exist "version.json" (
        for /f "tokens=4 delims=:," %%a in ('type version.json ^| findstr "version"') do set OLD_VER=%%a
        set OLD_VER=%OLD_VER:"=%
        set OLD_VER=%OLD_VER: =%
        set BUILD_TIME=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
        set BUILD_TIME=%BUILD_TIME: =0%
        echo Archiving existing dist to dist_v%OLD_VER%_%BUILD_TIME%...
        move dist dist_v%OLD_VER%_%BUILD_TIME%
    ) else (
        rmdir /s /q "dist"
    )
)
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

echo [2.1] Generating version information...
if exist "scripts\generate_version.py" (
    python scripts\generate_version.py
) else (
    echo Warning: generate_version.py not found.
)
echo Done.
echo.

echo [2.5] Setting up Virtual Environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to activate virtual environment.
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

    rem core.app
    move /Y app*.pyd src\app\core\ >nul 2>&1
    
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
set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
)

if exist "%ISCC%" (
    echo Found Inno Setup at: "%ISCC%"
    "%ISCC%" "scripts\msa_installer.iss"
    if errorlevel 1 (
        echo Installer creation failed!
        pause
    ) else (
        echo Installer created successfully in dist\
    )
) else (
    echo Warning: Inno Setup (ISCC.exe) not found.
    echo EXPECTED PATH: C:\Program Files (x86)\Inno Setup 6\ISCC.exe
    echo Please install Inno Setup 6 from https://jrsoftware.org/isdl.php
)

echo.
echo ======================================
echo Build Complete.
echo ======================================
pause

