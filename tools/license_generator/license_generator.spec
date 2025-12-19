
# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Define icon path
# We prefer standard .icns for macOS apps
icon_path = os.path.join('static', 'icon', 'icon.icns')
if not os.path.exists(icon_path):
    print(f"Warning: Icon not found at {icon_path}")
    # Fallback or None, usage depends on if file exists at build time
    # User script build_icon.sh should be run before build
    
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ui', 'ui'),
        ('core', 'core'),
        ('static/icon/logo.png', 'ui'), # Include logo for runtime usage
        ('serviceAccountKey.json', '.'), # Firebase Admin Key
    ],
    hiddenimports=[
        'sqlite3', 
        'csv', 
        'datetime', 
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'barcode',
        'barcode.writer',
        'weasyprint',
        'cffi',
        'html5lib',
        'cssselect2',
        'tinycss2'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MSALicenseMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MSALicenseMonitor',
)

app = BUNDLE(
    coll,
    name='MSALicenseMonitor.app',
    icon=icon_path,
    bundle_identifier='com.studiotai.msalicensemonitor',
)
