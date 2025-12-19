#!/bin/bash
# macOS Build Script for MSA Application
# This script builds a production-ready .app bundle for macOS

set -e  # Exit on error

echo "======================================"
echo "MSA macOS Build Script"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Error: This script must be run on macOS${NC}"
    exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}Step 1: Cleaning previous build artifacts...${NC}"
rm -rf build dist
echo -e "${GREEN}✓ Cleaned build directories${NC}"
echo ""

echo -e "${YELLOW}Step 2: Checking Python environment...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ Found $PYTHON_VERSION${NC}"
echo ""

echo -e "${YELLOW}Step 3: Checking/Installing PyInstaller...${NC}"
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip3 install pyinstaller
fi
PYINSTALLER_VERSION=$(python3 -c "import PyInstaller; print(PyInstaller.__version__)")
echo -e "${GREEN}✓ PyInstaller $PYINSTALLER_VERSION is installed${NC}"
echo ""

echo -e "${YELLOW}Step 4: Verifying dependencies...${NC}"
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: requirements.txt not found${NC}"
    exit 1
fi
echo "Installing/Updating dependencies..."
pip3 install -r requirements.txt --quiet
echo -e "${GREEN}✓ Dependencies verified${NC}"
echo ""

echo -e "${YELLOW}Step 5: Checking icon file...${NC}"
ICON_PATH="src/app/static/icons/AppIcon.icns"
if [ ! -f "$ICON_PATH" ]; then
    echo -e "${RED}Warning: Icon file not found at $ICON_PATH${NC}"
    echo "The app will be built without a custom icon"
else
    echo -e "${GREEN}✓ Icon file found${NC}"
fi
echo ""

echo -e "${YELLOW}Step 6: Updating version information...${NC}"
if [ -f "scripts/update_version.py" ]; then
    python3 scripts/update_version.py
    echo -e "${GREEN}✓ Version updated${NC}"
else
    echo -e "${YELLOW}⚠ Version update script not found, skipping...${NC}"
fi
echo ""

echo -e "${YELLOW}Step 6b: Compiling security modules (Cython)...${NC}"
if [ -f "build_cython.py" ]; then
    echo "Compiling modules..."
    python3 build_cython.py build_ext --inplace
    
    # Move compiled modules to correct locations for bundling
    # build_cython.py with --inplace puts them in root relative to package logic, but our setup matched root.
    # We need to move them to src/app/services/ and src/app/utils/security/
    
    echo "Moving compiled modules..."
    mv license_service.*.so src/app/services/ 2>/dev/null || true
    mv password_utils.*.so src/app/utils/security/ 2>/dev/null || true
    mv app.*.so src/app/core/ 2>/dev/null || true
    
    echo -e "${GREEN}✓ Cython modules compiled and placed${NC}"
else
    echo -e "${YELLOW}⚠ build_cython.py not found, skipping security hardening...${NC}"
fi
echo ""

echo -e "${YELLOW}Step 7: Building application with PyInstaller...${NC}"
echo "This may take several minutes..."
python3 -m PyInstaller release.spec --clean --noconfirm

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Build failed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Build completed successfully${NC}"
echo ""

echo -e "${YELLOW}Step 8: Verifying build output...${NC}"
APP_PATH="dist/MSA.app"
if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}✗ Application bundle not found at $APP_PATH${NC}"
    exit 1
fi

# Check app size
APP_SIZE=$(du -sh "$APP_PATH" | cut -f1)
echo -e "${GREEN}✓ Application bundle created: $APP_SIZE${NC}"
echo ""

echo -e "${YELLOW}Step 9: Creating DMG installer (optional)...${NC}"
DMG_NAME="MSA-Installer.dmg"
DMG_PATH="dist/$DMG_NAME"

# Remove old DMG if exists
if [ -f "$DMG_PATH" ]; then
    rm "$DMG_PATH"
fi

# Create DMG
echo "Creating disk image..."
hdiutil create -volname "MSA Installer" -srcfolder "$APP_PATH" -ov -format UDZO "$DMG_PATH"

if [ $? -eq 0 ]; then
    DMG_SIZE=$(du -sh "$DMG_PATH" | cut -f1)
    echo -e "${GREEN}✓ DMG created: $DMG_SIZE${NC}"
else
    echo -e "${YELLOW}⚠ DMG creation failed (optional step)${NC}"
fi
echo ""

echo "======================================"
echo -e "${GREEN}Build Complete!${NC}"
echo "======================================"
echo ""
echo "Build artifacts:"
echo "  • Application: $APP_PATH"
if [ -f "$DMG_PATH" ]; then
    echo "  • Installer:   $DMG_PATH"
fi
echo ""
echo "To test the application:"
echo "  open $APP_PATH"
echo ""
echo "To distribute:"
if [ -f "$DMG_PATH" ]; then
    echo "  Share the DMG file: $DMG_PATH"
else
    echo "  Compress the .app bundle and share it"
fi
echo ""
echo -e "${YELLOW}Note: For distribution outside the App Store, you may need to:${NC}"
echo "  1. Sign the application with your Apple Developer certificate"
echo "  2. Notarize the application with Apple"
echo "  3. Add entitlements for specific permissions"
echo ""
