#!/bin/bash
echo "🚀 Building License Generator for macOS..."

# Clean previous builds
rm -rf dist/LicenseGenerator.app dist/LicenseGenerator build

# Run PyInstaller with the spec file
python3 -m PyInstaller license_generator.spec --noconfirm --clean

# Ad-hoc sign / Remove quarantine (Fix for "Can't Open" on local dev machine)

echo "🔐 Applying local fix for 'can't open'..."
xattr -cr dist/LicenseGenerator.app

# Copy private key to persistent data folder for testing/usage
echo "🔑 Copying private key to Application Support..."
mkdir -p "$HOME/Library/Application Support/LicenseGenerator"
cp ../../private.pem "$HOME/Library/Application Support/LicenseGenerator/"


echo "✅ Build complete."
echo "📦 Application bundle: dist/LicenseGenerator.app"
echo "💡 If it still fails to open, try running: xattr -cr dist/LicenseGenerator.app"
