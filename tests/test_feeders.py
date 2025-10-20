"""
Test script for IEEE test feeders.

This module contains tests for loading and validating IEEE test feeder models.
"""

import os
import pytest
import opendssdirect as dss
from pathlib import Path
import tempfile
from typing import List

from opendss_mcp.utils.dss_wrapper import DSSCircuit

# Import test utilities
try:
    from .test_utils import create_bus_coords_file
except ImportError:
    # Fallback if the import fails (e.g., when running the test directly)
    import sys

    sys.path.append(str(Path(__file__).parent))
    from test_utils import create_bus_coords_file

# Path to the test feeders directory
TEST_FEEDERS_DIR = (
    Path(__file__).parent.parent / "src" / "opendss_mcp" / "data" / "ieee_feeders"
)

# Directory for temporary test files
TEST_TEMP_DIR = Path(__file__).parent / "temp"
TEST_TEMP_DIR.mkdir(exist_ok=True)

# Expected number of buses for each feeder
EXPECTED_BUS_COUNTS = {
    "IEEE13": 16,  # Actual bus count in the IEEE 13 bus feeder
    "IEEE34": 37,  # Actual bus count in the IEEE 34 bus feeder
    "IEEE123": 132,  # Actual bus count in the IEEE 123 bus feeder (includes regulators, transformers)
}

# Expected number of loads for each feeder
EXPECTED_LOAD_COUNTS = {
    "IEEE13": 15,  # Actual load count in the IEEE 13 bus feeder
    "IEEE34": 68,  # Actual load count in the IEEE 34 bus feeder (includes distributed loads)
    "IEEE123": 0,  # Load file not included in simplified version
}


@pytest.fixture(params=["IEEE13", "IEEE34", "IEEE123"])
def feeder_name(request):
    """Fixture to parameterize tests for each feeder."""
    return request.param


@pytest.fixture
def feeder_file(feeder_name):
    """Fixture to get the path to a feeder file."""
    return TEST_FEEDERS_DIR / f"{feeder_name}.dss"


def test_feeder_file_exists(feeder_file):
    """Test that the feeder file exists."""
    assert feeder_file.exists(), f"Feeder file {feeder_file} does not exist"


def get_bus_names(dss_circuit) -> List[str]:
    """Get all bus names from the circuit."""
    return dss.Circuit.AllBusNames()


def test_load_feeder(feeder_name, feeder_file):
    """Test loading a feeder and verify basic properties."""
    # Create a new DSS circuit
    dss_circuit = DSSCircuit()

    # Create a temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        # Load the feeder file
        assert dss_circuit.load_dss_file(str(feeder_file)), "Failed to load DSS file"

        # Get bus names and create a coordinate file
        bus_names = get_bus_names(dss_circuit)
        coords_file = create_bus_coords_file(bus_names, temp_dir)

        # Load the coordinate file
        dss.Text.Command(f"Buscoords {coords_file}")

        # Verify the circuit loaded successfully
        bus_count = dss.Circuit.NumBuses()
        assert bus_count > 0, "No buses found in the circuit"

        # Get circuit info
        load_count = dss.Loads.Count()

        # Verify bus count
        expected_buses = EXPECTED_BUS_COUNTS.get(feeder_name, 0)
        assert (
            bus_count == expected_buses
        ), f"Expected {expected_buses} buses, got {bus_count}"

        # Verify load count
        expected_loads = EXPECTED_LOAD_COUNTS.get(feeder_name, 0)
        assert (
            load_count == expected_loads
        ), f"Expected {expected_loads} loads, got {load_count}"


def test_power_flow(feeder_file):
    """Test running a power flow on the feeder."""
    # Create a new DSS circuit
    dss_circuit = DSSCircuit()

    # Create a temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        # Load the feeder file
        assert dss_circuit.load_dss_file(str(feeder_file)), "Failed to load DSS file"

        # Get bus names and create a coordinate file
        bus_names = get_bus_names(dss_circuit)
        coords_file = create_bus_coords_file(bus_names, temp_dir)

        # Load the coordinate file
        dss.Text.Command(f"Buscoords {coords_file}")

        # Configure solution settings
        dss.Solution.Mode(0)  # Snapshot mode
        dss.Solution.Number(1)
        dss.Solution.StepSize(0.1)

        # Run power flow
        dss.Solution.Solve()

        # Check if solution converged
        assert dss.Solution.Converged(), "Power flow did not converge"

        # Verify we can read circuit results
        total_power = dss.Circuit.TotalPower()
        assert len(total_power) == 2, "Should return [kW, kvar]"
        assert isinstance(total_power[0], (int, float)), "Total power should be numeric"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
