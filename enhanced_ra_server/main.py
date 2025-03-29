#!/usr/bin/env python3
"""
CLI entry point for Enhanced RA.Aid Server.

This module provides the command-line interface for starting the Enhanced RA.Aid Server,
including argument parsing and server initialization.
"""

import argparse
import uvicorn
from typing import Dict, Any

from enhanced_ra_server.config import load_config
from enhanced_ra_server.enhanced_server import EnhancedRAServer

__version__ = "0.1.0"


def main() -> None:
    """Parse command line arguments and start the Enhanced RA.Aid Server."""
    parser = argparse.ArgumentParser(
        description="Enhanced RA.Aid Server - Real-time WebSocket interface for RA.Aid"
    )
    
    # Basic server configuration
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind server (default: 8000)"
    )
    
    # AI model configuration
    parser.add_argument(
        "--model",
        help="Override default language model"
    )
    parser.add_argument(
        "--research-only",
        action="store_true",
        help="Run in research-only mode (skip planning and implementation)"
    )
    parser.add_argument(
        "--no-expert",
        action="store_true",
        help="Disable expert mode for simpler queries"
    )
    parser.add_argument(
        "--no-hil",
        action="store_true",
        help="Disable human-in-the-loop confirmations"
    )
    
    # Memory configuration
    parser.add_argument(
        "--memory-path",
        help="Path to memory database"
    )
    
    # Version information
    parser.add_argument(
        "--version",
        action="version",
        version=f"Enhanced RA.Aid Server v{__version__}"
    )
    
    args = parser.parse_args()
    
    # Convert arguments to configuration dictionary
    config = load_config(**vars(args))
    
    # Initialize the server
    server = EnhancedRAServer(config)
    
    # Start the server
    print(f"Starting Enhanced RA.Aid Server on {args.host}:{args.port}")
    uvicorn.run(server.app, host=args.host, port=args.port)


if __name__ == "__main__":
    main() 