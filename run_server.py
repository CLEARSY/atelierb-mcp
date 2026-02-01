#!/usr/bin/env python
"""Entry point script for running the MCP server."""

import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from atelierb_mcp.server import main

if __name__ == "__main__":
    main()
