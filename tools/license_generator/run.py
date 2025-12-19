#!/usr/bin/env python3
"""
MSA License Generator Launcher
Quick launcher script for the license generator tool
"""

import sys
import os

# Add the license generator directory to path
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOL_DIR)

# Import and run the main application
from main import main

if __name__ == "__main__":
    main()
