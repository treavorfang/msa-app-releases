#!/bin/bash

# Ensure we are in the project root or adjust paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
TOOL_DIR="$(dirname "$SCRIPT_DIR")"
ICON_DIR="$TOOL_DIR/static/icon"
SVG_FILE="$ICON_DIR/logo.svg"
ICNS_FILE="$ICON_DIR/icon.icns"
ICONSET_DIR="$ICON_DIR/icon.iconset"

# Check dependencies
if ! command -v rsvg-convert &> /dev/null; then
    echo "Error: rsvg-convert (librsvg) is not installed."
    echo "Please install it using Homebrew: brew install librsvg"
    exit 1
fi

if ! command -v iconutil &> /dev/null; then
    echo "Error: iconutil is not found (macOS required)."
    exit 1
fi

echo "Creating iconset directory..."
mkdir -p "$ICONSET_DIR"

echo "Converting SVG to PNGs..."
# Generate standard sizes
rsvg-convert -w 16 -h 16 "$SVG_FILE" -o "$ICONSET_DIR/icon_16x16.png"
rsvg-convert -w 32 -h 32 "$SVG_FILE" -o "$ICONSET_DIR/icon_16x16@2x.png"
rsvg-convert -w 32 -h 32 "$SVG_FILE" -o "$ICONSET_DIR/icon_32x32.png"
rsvg-convert -w 64 -h 64 "$SVG_FILE" -o "$ICONSET_DIR/icon_32x32@2x.png"
rsvg-convert -w 128 -h 128 "$SVG_FILE" -o "$ICONSET_DIR/icon_128x128.png"
rsvg-convert -w 256 -h 256 "$SVG_FILE" -o "$ICONSET_DIR/icon_128x128@2x.png"
rsvg-convert -w 256 -h 256 "$SVG_FILE" -o "$ICONSET_DIR/icon_256x256.png"
rsvg-convert -w 512 -h 512 "$SVG_FILE" -o "$ICONSET_DIR/icon_256x256@2x.png"
rsvg-convert -w 512 -h 512 "$SVG_FILE" -o "$ICONSET_DIR/icon_512x512.png"
rsvg-convert -w 1024 -h 1024 "$SVG_FILE" -o "$ICONSET_DIR/icon_512x512@2x.png"

echo "Packaging .icns file..."
iconutil -c icns "$ICONSET_DIR" -o "$ICNS_FILE"

# Clean up
rm -rf "$ICONSET_DIR"

echo "Success! Created $ICNS_FILE"

# Also regenerate the window icon (png) if needed
rsvg-convert -w 256 -h 256 "$SVG_FILE" -o "$ICON_DIR/logo.png"
echo "Created window icon $ICON_DIR/logo.png"
