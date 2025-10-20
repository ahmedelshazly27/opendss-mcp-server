"""Test utilities for OpenDSS MCP."""

from pathlib import Path
import tempfile
from typing import Dict, List, Optional


def create_bus_coords_file(bus_names: List[str], output_dir: Path) -> Path:
    """Create a minimal bus coordinate file for testing.

    Args:
        bus_names: List of bus names to include in the coordinate file
        output_dir: Directory to save the coordinate file

    Returns:
        Path to the created coordinate file
    """
    coords_file = output_dir / "buscoords.dss"
    with open(coords_file, "w") as f:
        for i, bus in enumerate(bus_names):
            # Simple grid layout for testing
            x = i * 100
            y = 0
            f.write(f"  {bus} {x} {y}\n")
    return coords_file
