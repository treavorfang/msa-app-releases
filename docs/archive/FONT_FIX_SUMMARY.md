# Font Warning Fix - Summary

## Issue

Qt was showing font warnings on macOS:

```
qt.qpa.fonts: Populating font family aliases took 317 ms.
Replace uses of missing font family "-apple-system" with one that exists to avoid this cost.

qt.text.font.db: OpenType support missing for "Roboto", script 11
```

## Root Cause

1. **CSS Stylesheets** used `-apple-system` and `Roboto` fonts which don't exist as named fonts in Qt
2. **Qt Font Resolution** was searching for these fonts on every startup, causing 300ms+ delay

## Solution Implemented

### 1. Updated Application Default Font

**File**: `/Users/studiotai/PyProject/msa/src/app/main.py`

Added explicit font configuration before QApplication initialization:

```python
from PySide6.QtGui import QFont

# Set default application font to avoid -apple-system font warning
default_font = QFont(".AppleSystemUIFont", 13)  # macOS system font
QApplication.setFont(default_font)
```

### 2. Updated Theme CSS Files

**Files**:

- `/Users/studiotai/PyProject/msa/src/app/static/theme/theme-dark.css`
- `/Users/studiotai/PyProject/msa/src/app/static/theme/theme-light.css`

**Before**:

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
  "Helvetica Neue", Arial, sans-serif;
```

**After**:

```css
font-family: ".AppleSystemUIFont", "Segoe UI", "Helvetica Neue", Arial,
  sans-serif;
```

## Font Stack Explanation

### `.AppleSystemUIFont`

- **macOS Native**: This is the actual system font identifier on macOS
- **Resolves to**: SF Pro Display/Text (macOS 10.11+)
- **No Search Delay**: Qt recognizes this immediately
- **Fallback Safe**: If not found, falls back to next font in stack

### Removed Fonts

- ❌ `-apple-system`: CSS-only identifier, not a real font name
- ❌ `BlinkMacSystemFont`: Blink engine specific, not needed
- ❌ `Roboto`: Google font, not installed by default on macOS

### Kept Fonts

- ✅ `"Segoe UI"`: Windows system font
- ✅ `"Helvetica Neue"`: macOS fallback
- ✅ `Arial`: Universal fallback
- ✅ `sans-serif`: Generic fallback

## Results

### Before

```
qt.qpa.fonts: Populating font family aliases took 317 ms.
qt.text.font.db: OpenType support missing for "Roboto", script 11
```

### After

✅ **No font warnings**
✅ **Faster startup** (saves ~300ms)
✅ **Native macOS fonts** used throughout
✅ **Consistent typography** across the application

## CSS Lint Warnings (Can Be Ignored)

The CSS linter shows warnings for Qt-specific properties:

- `subcontrol-origin` - Valid Qt CSS property
- `subcontrol-position` - Valid Qt CSS property
- `gridline-color` - Valid Qt CSS property
- `spacing` - Valid Qt CSS property
- `image` - Valid Qt CSS property

**These are NOT errors** - they are Qt-specific extensions to CSS that work perfectly in PySide6/Qt applications.

## Testing Checklist

- [x] Application starts without font warnings
- [x] Dark theme displays correctly
- [x] Light theme displays correctly
- [x] Text is readable and properly rendered
- [x] Myanmar/Burmese text still renders (Noto Sans Myanmar)
- [x] No performance degradation

---

**Date**: 2025-12-07
**Status**: ✅ Complete
**Impact**: Eliminated font warnings, improved startup time
