# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

# Determine icon path based on platform
icon_file = 'src/app/static/icons/logo.png'
# Windows prefers .ico
# Assume build_windows.bat handles conversion if needed, or we use logo.png and let PyInstaller convert
# Actually, best to have a .ico for Windows title bars etc.
if os.path.exists('src/app/static/icons/logo.ico'):
    icon_file = 'src/app/static/icons/logo.ico'


hidden_imports = [
    'peewee',
    'barcode',
    'barcode.writer',
    'PIL',
    'PIL.Image',
    'absl', 
    'absl.flags',
    'absl.app',
    'absl.logging',
    'Levenshtein',
    'dateutil',
    'pkg_resources',
    'charset_normalizer',
    'matplotlib',
    'matplotlib.pyplot',
    'matplotlib.backends.backend_qtagg',
    'matplotlib.backends.backend_qt5agg',
    'sqlite3',
    'phonenumbers',
    'psutil',
    'cryptography',
    'dotenv',
    'qrcode',
    'fpdf',
    'weasyprint',
    'cffi',
    'cssselect2',
    'html5lib',
    'tinycss2',
    'win32timezone' # Windows specific
]

a = Analysis(
    ['src/app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/app/static', 'static'),
        ('src/app/config/*.ini', 'config'),
        ('src/app/config/languages', 'config/languages'),
        ('src/app/config/*.flags', 'config'),
        ('plugins', 'plugins'),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# === CYTHON HARDENING ===
# Remove the source .py files for sensitive modules from the bundle
sensitive_modules = {
    'services.license_service',
    'utils.security.password_utils'
}

# Filter a.pure (which contains all python modules to be bundled as bytecode)
a.pure = [x for x in a.pure if x[0] not in sensitive_modules]

# Add the compiled extensions (.pyd) to binaries
import glob
def add_cython_module(module_name):
    # Convert module.name to path/to/name
    base_path = os.path.join('src', 'app', *module_name.split('.'))
    
    # Find the compiled file (e.g., name.pyd or name.cp39-win_amd64.pyd)
    dir_name = os.path.dirname(base_path)
    file_name = os.path.basename(base_path)
    
    # Check for .pyd with potential tags
    pattern = os.path.join(dir_name, file_name + "*.pyd")
    found = glob.glob(pattern)
    
    if found:
        src = found[0]
        
        # Calculate destination path in the bundle to preserve package structure
        # module 'services.license_service' -> 'services/license_service.pyd'
        dst_name = os.path.join(*module_name.split('.')) # services/license_service or services\license_service
        
        # We need the extension as well
        # Usually for Windows loading, we might want just .pyd or the full tagged name.
        # Python on Windows can load .cp311-win_amd64.pyd if it matches the interpreter.
        # However, to be safe/clean, usually exact match or same tag is fine.
        ext = os.path.basename(src).split('.', 1)[1]
        dst = f"{dst_name}.{ext}"
        
        print(f"Adding hardened module: {src} -> {dst}")
        a.binaries.append((dst, src, 'BINARY'))
    else:
        print(f"WARNING: Compiled module not found for {module_name}")

for mod in sensitive_modules:
    add_cython_module(mod)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MSA',
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
    icon=icon_file
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MSA',
)
