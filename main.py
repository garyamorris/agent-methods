#!/usr/bin/env python3
"""Convenience entry point for agent-methods."""
import sys
from pathlib import Path

# Add src to python path for direct execution
src_path = str(Path(__file__).resolve().parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from agent_methods.cli import main

if __name__ == "__main__":
    main()
