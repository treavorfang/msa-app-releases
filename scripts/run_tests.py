#!/usr/bin/env python3
"""
Test runner for Google 3X refactored components.

Usage:
    python3 run_tests.py              # Run all tests
    python3 run_tests.py --fast       # Run only fast tests
    python3 run_tests.py --coverage   # Run with coverage report
    python3 run_tests.py --verbose    # Verbose output
"""

import sys
import subprocess
from pathlib import Path

def run_tests(args=None):
    """Run pytest with specified arguments"""
    if args is None:
        args = []
    
    # Base pytest command
    cmd = [sys.executable, "-m", "pytest", "tests/"]
    
    # Add arguments
    cmd.extend(args)
    
    # Run tests
    print(f"Running: {' '.join(cmd)}")
    print("=" * 80)
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode

def main():
    """Main entry point"""
    args = sys.argv[1:]
    
    # Parse custom flags
    pytest_args = []
    
    if "--fast" in args:
        pytest_args.extend(["-v", "-m", "not slow"])
        args.remove("--fast")
    elif "--coverage" in args:
        pytest_args.extend([
            "--cov=src/app/views/tickets",
            "--cov-report=html",
            "--cov-report=term-missing",
            "-v"
        ])
        args.remove("--coverage")
    elif "--verbose" in args or "-v" in args:
        pytest_args.append("-v")
        if "--verbose" in args:
            args.remove("--verbose")
        if "-v" in args:
            args.remove("-v")
    else:
        # Default: verbose output
        pytest_args.append("-v")
    
    # Add remaining args
    pytest_args.extend(args)
    
    # Run tests
    exit_code = run_tests(pytest_args)
    
    if exit_code == 0:
        print("\n" + "=" * 80)
        print("✅ All tests passed!")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ Some tests failed!")
        print("=" * 80)
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
