# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

# Determine icon path based on platform
icon_file = 'src/app/static/icons/logo.png'
if sys.platform == 'darwin':
    # Use .icns for macOS
    icon_file = 'src/app/static/icons/AppIcon.icns'
elif sys.platform == 'win32':
    # Windows prefers .ico, but PyInstaller can convert .png
    icon_file = 'src/app/static/icons/logo.png'


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
    'matplotlib.backends.backend_qt5agg', # Keep for backward compat if needed
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
]

if sys.platform == 'win32':
    hidden_imports.append('win32timezone')

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
    'utils.security.password_utils',
    'core.app'
}

# Filter a.pure (which contains all python modules to be bundled as bytecode)
# x is (module_name, path_to_py_file, type_code)
# We want to remove the ones in sensitive_modules
a.pure = [x for x in a.pure if x[0] not in sensitive_modules]

# Add the compiled extensions (.so/.pyd) to binaries
# We assume they have been built and placed in the source tree
import glob
def add_cython_module(module_name):
    # Convert module.name to path/to/name
    base_path = os.path.join('src', 'app', *module_name.split('.'))
    
    # Find the compiled file (e.g., name.cpython-313-darwin.so or name.pyd)
    # We look in the directory where the .py file was
    dir_name = os.path.dirname(base_path)
    file_name = os.path.basename(base_path)
    
    pattern = os.path.join(dir_name, file_name + ".*.so") if sys.platform != 'win32' else os.path.join(dir_name, file_name + ".*.pyd")
    found = glob.glob(pattern)
    
    if not found:
        # Fallback for Windows typically just .pyd without big tags sometimes, or with tags
        pattern_win = os.path.join(dir_name, file_name + ".pyd")
        found = glob.glob(pattern_win)
        
    if found:
        # We take the first match
        src = found[0]
        # Destination in the bundle should be the file name, usually valid with the tag
        # But we place it in the folder structure matching the package
        # module 'services.license_service' -> 'services/license_service.cpython-....so'
        # PyInstaller binaries tuple: (dest_name, src_path, 'BINARY')
        # dest_name should be relative to the bundle top level? or inside?
        # Typically binaries are put at top level or specific folders.
        # For python extensions to be imported as 'services.license_service', they usually
        # need to be in 'services' subdir if 'services' is a package.
        
        # However, PyInstaller collects binaries in the top level usually unless specified.
        # But if we want `import services.license_service` to work:
        # 1. 'services' must be a package (it is).
        # 2. The .so must be in 'services/' folder in the frozen app.
        
        # PyInstaller puts many binaries in top level content config.
        # Let's try attempting to preserve the path structure for these specific binaries.
        
        dst_name = os.path.join(*module_name.split('.')) # services/license_service
        # We need the extension as well
        ext = os.path.basename(src).split('.', 1)[1] # cpython-313-darwin.so
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
    argv_emulation=True, # Improved Mac integration
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

# Load version info
import runpy
version_path = os.path.join(os.getcwd(), 'src', 'app', 'version.py')
version_data = runpy.run_path(version_path)
app_version = version_data.get('VERSION', '1.0.0')
build_number = str(version_data.get('BUILD_NUMBER', '0'))

app = BUNDLE(
    coll,
    name='MSA.app',
    icon=icon_file,
    bundle_identifier='com.studiotai.msa',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'LSBackgroundOnly': 'False',
        'CFBundleShortVersionString': app_version,
        'CFBundleVersion': build_number,
        'CFBundleName': 'MSA',
        'CFBundleDisplayName': 'MSA',
        'CFBundleIconFile': 'AppIcon.icns',
        'LSMinimumSystemVersion': '11.0',
    },
)
