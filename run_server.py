#!/usr/bin/env python3
"""
Convenience script to run the Enhanced RA.Aid Server.

Example usage:
    python run_server.py --host 127.0.0.1 --port 8000 --memory-path memory.db
"""

from enhanced_ra_server.main import main

if __name__ == "__main__":
    main() 