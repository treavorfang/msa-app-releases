from setuptools import setup
from Cython.Build import cythonize
import os
import shutil

# Define modules to compile
# We use relative paths from the root where this script is run
MODULES_TO_COMPILE = [
    "src/app/services/license_service.py",
    "src/app/utils/security/password_utils.py",
    "src/app/core/app.py"
]

# Clean up previous builds
if os.path.exists("build"):
    shutil.rmtree("build")

try:
    setup(
        name='MSA Security Modules',
        ext_modules=cythonize(
            MODULES_TO_COMPILE,
            compiler_directives={'language_level': "3", 'always_allow_keywords': True},
            build_dir="build",  # Build in a separate directory
            quiet=False
        ),
    )
    print("Cython compilation successful.")
except Exception as e:
    print(f"Cython compilation failed: {e}")
