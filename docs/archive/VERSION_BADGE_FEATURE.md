# Version Badge Feature

## Overview

The About dialog now displays a version type badge that automatically detects whether the application is running with a developer/beta license or a production license.

## Badge Types

### 🟠 BETA Badge (Orange)

- **Color**: `#F59E0B` (Orange)
- **Displayed when**: License name contains any of these keywords:
  - "developer"
  - "dev"
  - "beta"
  - "test"
  - "studio tai"
- **Tooltip**: "Developer/Beta License"
- **Use case**: Internal testing, development builds, beta testing

### 🟢 RELEASE Badge (Green)

- **Color**: `#10B981` (Green)
- **Displayed when**: Valid production license (doesn't match developer keywords)
- **Tooltip**: "Production License"
- **Use case**: Customer deployments, production environments

### 🔴 UNLICENSED Badge (Red)

- **Color**: `#EF4444` (Red)
- **Displayed when**: No valid license found or license validation fails
- **Use case**: Trial mode, expired licenses, invalid licenses

## Implementation Details

### Location

- **File**: `/src/app/views/dialogs/about_dialog.py`
- **Method**: `_get_version_type_badge()`
- **Display**: About Dialog header, next to version number

### Detection Logic

```python
# Checks license name (case-insensitive)
is_developer = any(keyword in license_name for keyword in
    ['developer', 'dev', 'beta', 'test', 'studio tai'])
```

### Visual Layout

The badge appears in the About dialog header:

```
MSA
[v1.0.0] [BETA] Build 305 • 2025-12-10
```

## Usage Examples

### Developer License

If you generate a license with name "Studio Tai Developer" or "Beta Tester":

- Badge shows: **BETA** (orange)
- Indicates this is a development/testing version

### Production License

If you generate a license with name "World Lock Mobile 2" or "Customer Name":

- Badge shows: **RELEASE** (green)
- Indicates this is a production deployment

## Benefits

1. **Clear Identification**: Users and support staff can immediately see if they're running a beta or production version
2. **Automatic Detection**: No manual configuration needed - determined from license
3. **Visual Distinction**: Color-coded badges make it easy to distinguish at a glance
4. **Professional**: Matches modern software distribution practices

## Testing

To test different badge types:

1. **Beta Badge**: Use your current "Studio Tai" developer license
2. **Release Badge**: Generate a license with a customer name (e.g., "ABC Company")
3. **Unlicensed Badge**: Delete or rename the license file

## Future Enhancements

Possible additions:

- Add build type (Debug/Release) detection
- Show git branch name for developer builds
- Add expiry countdown for time-limited licenses
- Custom badge colors per license tier (Basic/Pro/Enterprise)
