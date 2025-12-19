# macOS Build Guide for MSA Application

This guide will help you build a production-ready macOS application bundle (.app) for the MSA application.

## Prerequisites

### 1. System Requirements

- **macOS**: 11.0 (Big Sur) or later
- **Python**: 3.8 or later
- **Xcode Command Line Tools**: Required for some dependencies

To install Xcode Command Line Tools:

```bash
xcode-select --install
```

### 2. Python Environment

Ensure you have Python 3 installed:

```bash
python3 --version
```

### 3. Dependencies

Install all required Python packages:

```bash
pip3 install -r requirements.txt
pip3 install pyinstaller
```

## Building the Application

### Quick Build (Recommended)

Simply run the build script:

```bash
./build_macos.sh
```

This script will:

1. Clean previous build artifacts
2. Verify Python environment
3. Install/update PyInstaller
4. Verify all dependencies
5. Build the application bundle
6. Create a DMG installer (optional)

### Manual Build

If you prefer to build manually:

1. **Clean previous builds:**

   ```bash
   rm -rf build dist
   ```

2. **Build with PyInstaller:**

   ```bash
   python3 -m PyInstaller release.spec --clean --noconfirm
   ```

3. **Find your application:**
   The built application will be at: `dist/MSA.app`

## Build Output

After a successful build, you'll find:

- **Application Bundle**: `dist/MSA.app`
- **DMG Installer**: `dist/MSA-Installer.dmg` (if created)

## Testing the Build

### Test Locally

```bash
open dist/MSA.app
```

### Verify Application Info

```bash
# Check bundle structure
ls -la dist/MSA.app/Contents/

# Check Info.plist
plutil -p dist/MSA.app/Contents/Info.plist

# Check app signature (if signed)
codesign -dvv dist/MSA.app
```

## Distribution

### For Internal Testing

1. **Compress the .app bundle:**

   ```bash
   cd dist
   zip -r MSA.app.zip MSA.app
   ```

2. Share the ZIP file with testers

### For Public Distribution

For distributing outside your organization, you'll need to:

1. **Sign the Application**

   - Requires an Apple Developer account ($99/year)
   - Use your Developer ID Application certificate

   ```bash
   codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/MSA.app
   ```

2. **Notarize the Application**

   - Required for macOS 10.15+ (Catalina and later)
   - Prevents "unidentified developer" warnings

   ```bash
   # Create a ZIP for notarization
   ditto -c -k --keepParent dist/MSA.app MSA.zip

   # Submit for notarization
   xcrun notarytool submit MSA.zip --apple-id "your@email.com" --team-id "TEAMID" --password "app-specific-password"

   # Staple the notarization ticket
   xcrun stapler staple dist/MSA.app
   ```

3. **Create a Signed DMG**
   ```bash
   hdiutil create -volname "MSA Installer" -srcfolder dist/MSA.app -ov -format UDZO dist/MSA-Installer.dmg
   codesign --sign "Developer ID Application: Your Name" dist/MSA-Installer.dmg
   ```

## Troubleshooting

### Build Fails with "Module Not Found"

- Ensure all dependencies are installed: `pip3 install -r requirements.txt`
- Check `release.spec` for missing hidden imports
- Add missing modules to the `hiddenimports` list in `release.spec`

### Application Won't Open

- Check Console.app for error messages
- Verify the app bundle structure: `ls -R dist/MSA.app/Contents/`
- Test from terminal to see error output: `dist/MSA.app/Contents/MacOS/MSA`

### "App is Damaged" Error

- This usually means the app needs to be signed or notarized
- For testing, users can bypass this with: `xattr -cr dist/MSA.app`
- For distribution, properly sign and notarize the app

### Icon Not Showing

- Verify `AppIcon.icns` exists at: `src/app/static/icons/AppIcon.icns`
- Check the icon is referenced in `release.spec`
- Clear icon cache: `sudo rm -rf /Library/Caches/com.apple.iconservices.store`

### Large Application Size

- The initial build may be 200-400 MB due to Python runtime and dependencies
- This is normal for PyInstaller-built applications
- The DMG will compress this significantly

## Build Configuration

The build is configured in `release.spec`:

### Key Settings

- **Entry Point**: `src/app/main.py`
- **App Name**: MSA
- **Bundle ID**: com.studiotai.msa
- **Icon**: `src/app/static/icons/AppIcon.icns`
- **Minimum macOS**: 11.0 (Big Sur)

### Included Resources

- Static files (icons, images)
- Configuration files (\*.ini)
- Language files
- Database migrations
- License public key

## Version Management

The application version is defined in `src/app/version.py`:

- **VERSION**: Semantic version (e.g., "1.0.0")
- **BUILD_NUMBER**: Auto-incremented build number
- **GIT_COMMIT**: Git commit hash (if available)

## Advanced Options

### Universal Binary (Intel + Apple Silicon)

To build a universal binary that runs on both Intel and Apple Silicon Macs:

1. Install PyInstaller with universal2 support
2. Modify `release.spec`:
   ```python
   exe = EXE(
       ...
       target_arch='universal2',
       ...
   )
   ```

### Custom Entitlements

For apps requiring special permissions (camera, microphone, etc.):

1. Create `entitlements.plist`:

   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
       <true/>
   </dict>
   </plist>
   ```

2. Update `release.spec`:
   ```python
   exe = EXE(
       ...
       entitlements_file='entitlements.plist',
       ...
   )
   ```

## CI/CD Integration

For automated builds using GitHub Actions or similar:

```yaml
name: Build macOS

on: [push, pull_request]

jobs:
  build:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: "3.10"
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      - name: Build application
        run: ./build_macos.sh
      - name: Upload artifact
        uses: actions/upload-artifact@v2
        with:
          name: MSA-macOS
          path: dist/MSA.app
```

## Support

For build issues:

1. Check the build log for specific errors
2. Verify all prerequisites are installed
3. Ensure you're using a compatible macOS version
4. Review the PyInstaller documentation: https://pyinstaller.org/

## Additional Resources

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [Apple Developer Documentation](https://developer.apple.com/documentation/)
- [Code Signing Guide](https://developer.apple.com/support/code-signing/)
- [Notarization Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
