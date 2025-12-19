# Windows Build Guide

## Prerequisites

### Required Software

1. **Python 3.10 or higher**

   - Download from: https://www.python.org/downloads/
   - **Important**: Check "Add Python to PATH" during installation
   - Verify installation: `python --version`

2. **Git** (for version control)

   - Download from: https://git-scm.com/download/win
   - Or use GitHub Desktop: https://desktop.github.com/

3. **Visual C++ Redistributable** (usually already installed)
   - Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Optional Software

1. **Inno Setup** (for creating installers)

   - Download from: https://jrsoftware.org/isdl.php
   - Install to default location: `C:\Program Files (x86)\Inno Setup 6\`

2. **Code Signing Certificate** (for production distribution)

   - Required for Windows SmartScreen bypass
   - Purchase from: DigiCert, Sectigo, or other CA

3. **GTK3 Runtime** (Required for PDF Generation)
   - **Crucial for WeasyPrint**: The app uses WeasyPrint for invoice generation, which requires the GTK3 libraries.
   - Download the **GTK3 Runtime for Windows** (64-bit):
     - Source: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
     - File: `gtk3-runtime-x.x.x.x-x-x-ts-win64.exe`
   - **Installation**:
     - Run the installer.
     - **Important**: Ensure "Set up PATH environment variable" is checked during installation.
   - **Verification**:
     - Open a new Command Prompt and run `where libcairo-2.dll`. It should return a path.

## Quick Build

### Option 1: Using the Build Script (Recommended)

1. **Open Command Prompt** in the project directory

   ```cmd
   cd C:\path\to\msa
   ```

2. **Run the build script**

   ```cmd
   build_windows.bat
   ```

3. **Wait for completion** (3-5 minutes)

4. **Find your executable**
   ```
   dist\MSA\MSA.exe
   ```

### Option 2: Manual Build

1. **Install dependencies**

   ```cmd
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. **Build with PyInstaller**

   ```cmd
   pyinstaller release.spec --noconfirm --clean
   ```

3. **Find your executable**
   ```
   dist\MSA\MSA.exe
   ```

## Build Process Details

### Step-by-Step Breakdown

The build script performs the following steps:

1. **Clean Previous Builds**

   - Removes `build/` directory
   - Removes `dist/` directory

2. **Verify Python**

   - Checks Python installation
   - Verifies version (3.10+)

3. **Install PyInstaller**

   - Checks if already installed
   - Installs if missing

4. **Install Dependencies**

   - Installs from `requirements.txt`
   - Includes all required packages

5. **Verify Icon**

   - Checks for `src/app/static/icons/logo.png`
   - Warns if missing

6. **Update Version** (optional)

   - Runs `scripts/update_version.py`
   - Updates build number

7. **Build Application**

   - Runs PyInstaller with `release.spec`
   - Creates executable and dependencies

8. **Verify Output**

   - Checks `dist/MSA/MSA.exe` exists
   - Reports file size

9. **Create Installer** (optional)
   - Uses Inno Setup if installed
   - Creates `MSA-Setup.exe`

### Build Output

After successful build:

```
dist/
└── MSA/
    ├── MSA.exe              (Main executable)
    ├── python313.dll        (Python runtime)
    ├── _internal/           (Dependencies)
    │   ├── PySide6/
    │   ├── matplotlib/
    │   ├── reportlab/
    │   └── ... (other packages)
    ├── static/              (App resources)
    │   ├── icons/
    │   ├── images/
    │   └── styles/
    └── config/              (Configuration files)
        └── languages/
```

**Total size**: ~180-200 MB

## Testing the Build

### On Your Development Machine

1. **Run the executable**

   ```cmd
   dist\MSA\MSA.exe
   ```

2. **Test all features**
   - Login
   - Create tickets
   - Generate reports
   - Print documents
   - All tabs and dialogs

### On a Clean Windows Machine

**Important**: Always test on a clean machine without Python installed!

1. **Copy the entire `dist\MSA\` folder** to the test machine

2. **Run `MSA.exe`**

3. **Verify**:
   - Application starts without errors
   - All features work
   - No missing dependencies
   - Performance is acceptable

## Distribution Options

### Option 1: Zip File (Simple)

**Pros**: Simple, no installer needed
**Cons**: User must extract, less professional

**Steps**:

1. Zip the entire `dist\MSA\` folder
2. Name it `MSA-v1.0.0-Windows.zip`
3. Share the zip file

**User Installation**:

1. Extract zip to desired location
2. Run `MSA.exe`
3. Create desktop shortcut if desired

### Option 2: Inno Setup Installer (Recommended)

**Pros**: Professional, easy installation, auto-updates
**Cons**: Requires Inno Setup

**Steps**:

1. **Install Inno Setup**

   - Download from: https://jrsoftware.org/isdl.php

2. **Create installer script** (`installer/windows_installer.iss`):

   ```iss
   [Setup]
   AppName=MSA
   AppVersion=1.0.0
   DefaultDirName={autopf}\MSA
   DefaultGroupName=MSA
   OutputDir=dist
   OutputBaseFilename=MSA-Setup
   Compression=lzma2
   SolidCompression=yes

   [Files]
   Source: "dist\MSA\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

   [Icons]
   Name: "{group}\MSA"; Filename: "{app}\MSA.exe"
   Name: "{autodesktop}\MSA"; Filename: "{app}\MSA.exe"

   [Run]
   Filename: "{app}\MSA.exe"; Description: "Launch MSA"; Flags: nowait postinstall skipifsilent
   ```

3. **Compile installer**

   ```cmd
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\windows_installer.iss
   ```

4. **Find installer**
   ```
   dist\MSA-Setup.exe
   ```

### Option 3: NSIS Installer (Alternative)

**Pros**: Highly customizable, free
**Cons**: More complex setup

**Download**: https://nsis.sourceforge.io/Download

### Option 4: MSI Installer (Enterprise)

**Pros**: Group Policy deployment, enterprise-friendly
**Cons**: Complex, requires WiX Toolset

**Download**: https://wixtoolset.org/

## Code Signing (Production)

### Why Sign Your Application?

- **Windows SmartScreen**: Prevents "Unknown Publisher" warnings
- **User Trust**: Shows verified publisher
- **Security**: Prevents tampering

### How to Sign

1. **Purchase Certificate**

   - DigiCert: https://www.digicert.com/
   - Sectigo: https://sectigostore.com/
   - Cost: ~$200-500/year

2. **Install Certificate**

   - Import to Windows Certificate Store

3. **Sign Executable**

   ```cmd
   signtool sign /a /t http://timestamp.digicert.com dist\MSA\MSA.exe
   ```

4. **Verify Signature**
   ```cmd
   signtool verify /pa dist\MSA\MSA.exe
   ```

## Troubleshooting

### Build Fails

**Error**: `Python is not installed or not in PATH`
**Solution**: Reinstall Python with "Add to PATH" checked

**Error**: `ModuleNotFoundError: No module named 'xxx'`
**Solution**: Add to `hiddenimports` in `release.spec`

**Error**: `FileNotFoundError: icon file not found`
**Solution**: Ensure `src/app/static/icons/logo.png` exists

### Application Won't Start

**Error**: `VCRUNTIME140.dll not found`
**Solution**: Install Visual C++ Redistributable

**Error**: `Application crashes on startup`
**Solution**:

1. Run from command prompt to see errors
2. Check `dist\MSA\_internal\` for missing files
3. Test on clean machine

### Performance Issues

**Issue**: Slow startup
**Solution**: Already optimized with lazy loading!

**Issue**: Large file size
**Solution**:

1. Remove unused packages from `requirements.txt`
2. Use UPX compression (already enabled)
3. Exclude unnecessary data files

## Advanced Configuration

### Custom Icon

1. **Create `.ico` file** (256x256 recommended)

   - Use online converter: https://convertio.co/png-ico/

2. **Update `release.spec`**
   ```python
   icon_file = 'src/app/static/icons/app_icon.ico'
   ```

### Version Information

Edit `src/app/version.py`:

```python
VERSION = "1.0.0"
BUILD_NUMBER = 1
COMPANY_NAME = "Your Company"
COPYRIGHT = "Copyright © 2025"
```

### Exclude Files

To reduce size, exclude unnecessary files in `release.spec`:

```python
excludes=[
    'tkinter',
    'unittest',
    'test',
    'email',
    'http',
    'xml',
]
```

## Build Checklist

Before distributing:

- [ ] Test on development machine
- [ ] Test on clean Windows machine
- [ ] Verify all features work
- [ ] Check file size is reasonable
- [ ] Test installation process
- [ ] Verify uninstallation works
- [ ] Check for antivirus false positives
- [ ] Test on Windows 10 and 11
- [ ] Verify license validation
- [ ] Test auto-updates (if implemented)

## Performance Optimizations Included

This build includes all performance optimizations:

✅ **Lazy Tab Creation** - 3-5x faster main window
✅ **Background Preloading** - Eliminates cold start delay
✅ **Progress Bar Feedback** - Shows initialization status
✅ **Instant Login** - No fake delays

**Expected Performance**:

- First launch: 1-2 seconds to login screen
- Login: Instant (~50ms)
- Main window: 0.5-1 second
- Tab switching: Instant (after first access)

## Support

### Common Issues

1. **Windows Defender blocks app**

   - Solution: Code sign the executable

2. **SmartScreen warning**

   - Solution: Code sign with EV certificate

3. **Antivirus false positive**
   - Solution: Submit to antivirus vendors for whitelisting

### Getting Help

- Check PyInstaller docs: https://pyinstaller.org/
- Windows packaging guide: https://packaging.python.org/
- Inno Setup docs: https://jrsoftware.org/ishelp/

## Next Steps

1. **Build the application**

   ```cmd
   build_windows.bat
   ```

2. **Test thoroughly**

3. **Create installer** (optional)

4. **Sign executable** (for production)

5. **Distribute to users**

---

**Ready to build?** Run `build_windows.bat` and you'll have a production-ready Windows application in minutes! 🚀
