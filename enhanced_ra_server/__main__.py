#!/usr/bin/env python3
"""
Package entry point for Enhanced RA.Aid Server.

This module allows running the Enhanced RA.Aid Server directly
with `python -m enhanced_ra_server`.
"""

import os
import sys

# Add the parent directory to the Python path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import the main function
from enhanced_ra_server.main import main

if __name__ == "__main__":
    main() 