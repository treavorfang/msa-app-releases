#!/bin/bash
echo "🚀 Building MSA License Monitor for macOS..."

# Clean previous builds
echo "Cleaning up..."
rm -rf dist build *.app

# Run PyInstaller with the spec file
python3 -m PyInstaller license_generator.spec --noconfirm --clean

# Ad-hoc sign / Remove quarantine (Fix for "Can't Open" on local dev machine)

echo "🔐 Applying local fix for 'can't open'..."
xattr -cr dist/MSALicenseMonitor.app




echo "✅ Build complete."
echo "📦 Application bundle: dist/MSALicenseMonitor.app"
echo "💡 If it still fails to open, try running: xattr -cr dist/MSALicenseMonitor.app"
