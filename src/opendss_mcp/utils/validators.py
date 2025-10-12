"""
Input validation utilities for OpenDSS MCP operations.

This module provides validation functions for common input parameters used in
OpenDSS circuit operations, with detailed error messages for debugging.
"""

from typing import Optional

# Type alias for better readability
from .dss_wrapper import DSSCircuit

# Constants for validation
VALID_FEEDER_IDS = ["IEEE13", "IEEE34", "IEEE123"]
MIN_VOLTAGE_PU = 0.8
MAX_VOLTAGE_PU = 1.2


def validate_bus_id(bus_id: str, dss_circuit: DSSCircuit) -> None:
    """Validate that a bus ID exists in the current circuit.

    Args:
        bus_id: The bus ID to validate
        dss_circuit: An instance of DSSCircuit to check against

    Raises:
        ValueError: If the bus ID is not found in the circuit
        RuntimeError: If there's an error accessing circuit buses
    """
    try:
        available_buses = dss_circuit.get_bus_names()
        if bus_id not in available_buses:
            sample_buses = ", ".join(available_buses[:5])
            raise ValueError(
                f"Bus '{bus_id}' not found in circuit. "
                f"Available buses (first 5): {sample_buses}..."
            )
    except Exception as e:
        raise RuntimeError(f"Error validating bus ID '{bus_id}': {str(e)}") from e


def validate_positive_float(value: float, name: str) -> None:
    """Validate that a numeric value is positive.

    Args:
        value: The value to validate
        name: The name of the parameter (used in error message)

    Raises:
        ValueError: If the value is not a positive number
    """
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"{name} must be a positive number, got {value}")


def validate_voltage_limits(min_pu: float, max_pu: float) -> None:
    """Validate voltage limits are within acceptable range and min < max.

    Args:
        min_pu: Minimum voltage in per-unit
        max_pu: Maximum voltage in per-unit

    Raises:
        ValueError: If voltage limits are outside valid range or min >= max
    """
    if not (MIN_VOLTAGE_PU <= min_pu < max_pu <= MAX_VOLTAGE_PU):
        raise ValueError(
            f"Voltage limits must satisfy {MIN_VOLTAGE_PU} ≤ min_pu ({min_pu}) < "
            f"max_pu ({max_pu}) ≤ {MAX_VOLTAGE_PU}"
        )


def validate_feeder_id(feeder_id: str) -> None:
    """Validate that the feeder ID is one of the supported IEEE test feeders.

    Args:
        feeder_id: The feeder ID to validate

    Raises:
        ValueError: If the feeder ID is not in the list of supported feeders
    """
    if feeder_id not in VALID_FEEDER_IDS:
        valid_options = ", ".join(f'"{f}"' for f in VALID_FEEDER_IDS)
        raise ValueError(
            f"Unsupported feeder ID: '{feeder_id}'. "
            f"Valid options are: {valid_options}"
        )
