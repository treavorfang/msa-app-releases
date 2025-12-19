
import PyInstaller.__main__
import os
import shutil
import sys

# Define base directory (tools/license_generator)
base_dir = os.path.dirname(os.path.abspath(__file__))

# Change working directory to base_dir to make relative paths in .spec work
os.chdir(base_dir)

# Clean previous builds
dist_dir = os.path.join(base_dir, "dist")
build_dir = os.path.join(base_dir, "build")

if os.path.exists(dist_dir):
    shutil.rmtree(dist_dir)
if os.path.exists(build_dir):
    shutil.rmtree(build_dir)

print(f"Building License Generator from {base_dir}...")

# Run PyInstaller with the spec file
PyInstaller.__main__.run([
    'license_generator.spec',
    '--noconfirm',
    '--clean'
])

print("Build complete. Output in tools/license_generator/dist/")
