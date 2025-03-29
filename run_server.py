#!/usr/bin/env python3
"""
Launch script for Enhanced RA.Aid Server.

This script provides a convenient way to start the server without
installing it as a package.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the main function
from enhanced_ra_server.main import main

if __name__ == "__main__":
    main() 