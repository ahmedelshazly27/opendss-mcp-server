"""
Voltage violation checking module for OpenDSS.

This module provides functions for checking bus voltages against specified limits
and identifying violations with severity classification.
"""

import logging
from typing import Any, Dict, List, Optional

import opendssdirect as dss

from ..utils.formatters import format_success_response, format_error_response
from ..utils.validators import validate_voltage_limits

logger = logging.getLogger(__name__)


def _calculate_severity(deviation_pu: float) -> str:
    """Calculate violation severity based on deviation magnitude.

    Args:
        deviation_pu: Absolute deviation from limit in per-unit

    Returns:
        Severity classification: "minor", "moderate", or "severe"
    """
    abs_deviation = abs(deviation_pu)
    if abs_deviation < 0.02:
        return "minor"
    elif abs_deviation < 0.05:
        return "moderate"
    else:
        return "severe"


def _get_bus_voltages_by_phase() -> Dict[str, Dict[str, float]]:
    """Get voltage magnitudes for all buses organized by phase.

    Returns:
        Dictionary mapping bus names to phase voltages in per-unit
        Format: {bus_name: {phase: voltage_pu, ...}}
    """
    bus_voltages = {}

    try:
        # Get all bus names
        all_buses = dss.Circuit.AllBusNames()

        for bus_name in all_buses:
            dss.Circuit.SetActiveBus(bus_name)

            # Get voltage magnitudes and angles (interleaved array)
            volts = dss.Bus.puVmagAngle()

            if not volts:
                continue

            # Get number of nodes (phases) at this bus
            num_nodes = dss.Bus.NumNodes()

            # Extract phase voltages (magnitudes only, skip angles)
            phase_voltages = {}
            phase_names = ['1', '2', '3']  # Standard phase naming

            for i in range(min(num_nodes, 3)):  # Limit to 3 phases
                if i * 2 < len(volts):
                    voltage_pu = volts[i * 2]  # Skip angles (odd indices)
                    phase_voltages[phase_names[i]] = voltage_pu

            if phase_voltages:
                bus_voltages[bus_name.lower()] = phase_voltages

    except Exception as e:
        logger.error(f"Error getting bus voltages: {e}")

    return bus_voltages


def check_voltage_violations(
    min_voltage_pu: float = 0.95,
    max_voltage_pu: float = 1.05,
    phase: Optional[str] = None
) -> Dict[str, Any]:
    """Check all bus voltages against specified limits and identify violations.

    This function analyzes the voltage profile from the last power flow solution
    and identifies buses that exceed the specified voltage limits. Each violation
    is classified by severity based on the magnitude of deviation.

    Args:
        min_voltage_pu: Minimum acceptable voltage in per-unit (default: 0.95)
        max_voltage_pu: Maximum acceptable voltage in per-unit (default: 1.05)
        phase: Optional phase filter ('1', '2', '3', or None for all phases)

    Returns:
        Dictionary containing:
            - success: Boolean indicating if the operation was successful
            - data: Dictionary with violations list and summary statistics
            - metadata: Additional metadata about the analysis
            - errors: List of error messages if any occurred

    Example:
        >>> result = check_voltage_violations(min_voltage_pu=0.95, max_voltage_pu=1.05)
        >>> if result['success']:
        ...     violations = result['data']['violations']
        ...     print(f"Found {len(violations)} voltage violations")
    """
    try:
        # Validate voltage limits
        validate_voltage_limits(min_voltage_pu, max_voltage_pu)

        # Validate phase parameter if provided
        if phase is not None and phase not in ['1', '2', '3']:
            return format_error_response(
                f"Invalid phase '{phase}'. Must be '1', '2', '3', or None for all phases."
            )

        # Check if a circuit is loaded
        if not dss.Circuit.Name():
            return format_error_response(
                "No circuit loaded. Please load a feeder first using load_feeder tool."
            )

        # Get bus voltages organized by phase
        bus_voltages = _get_bus_voltages_by_phase()

        if not bus_voltages:
            return format_error_response(
                "No voltage data available. Please run power flow analysis first."
            )

        # Find violations
        violations: List[Dict[str, Any]] = []

        for bus_name, phase_voltages in bus_voltages.items():
            for phase_id, voltage_pu in phase_voltages.items():
                # Skip if filtering by phase and this isn't the target phase
                if phase is not None and phase_id != phase:
                    continue

                violation_type = None
                deviation_pu = 0.0

                if voltage_pu < min_voltage_pu:
                    violation_type = "undervoltage"
                    deviation_pu = voltage_pu - min_voltage_pu
                elif voltage_pu > max_voltage_pu:
                    violation_type = "overvoltage"
                    deviation_pu = voltage_pu - max_voltage_pu

                if violation_type:
                    severity = _calculate_severity(deviation_pu)

                    violations.append({
                        "bus": bus_name,
                        "phase": phase_id,
                        "voltage_pu": round(voltage_pu, 6),
                        "violation_type": violation_type,
                        "deviation_pu": round(deviation_pu, 6),
                        "severity": severity
                    })

        # Sort violations by absolute deviation (worst first)
        violations.sort(key=lambda x: abs(x["deviation_pu"]), reverse=True)

        # Create summary statistics
        num_violations = len(violations)
        num_undervoltage = sum(1 for v in violations if v["violation_type"] == "undervoltage")
        num_overvoltage = sum(1 for v in violations if v["violation_type"] == "overvoltage")

        # Count by severity
        severity_counts = {
            "minor": sum(1 for v in violations if v["severity"] == "minor"),
            "moderate": sum(1 for v in violations if v["severity"] == "moderate"),
            "severe": sum(1 for v in violations if v["severity"] == "severe")
        }

        # Find worst violation
        worst_violation = violations[0] if violations else None

        # Prepare response data
        data = {
            "violations": violations,
            "summary": {
                "total_violations": num_violations,
                "undervoltage_count": num_undervoltage,
                "overvoltage_count": num_overvoltage,
                "severity_counts": severity_counts,
                "worst_violation": worst_violation
            },
            "limits": {
                "min_voltage_pu": min_voltage_pu,
                "max_voltage_pu": max_voltage_pu,
                "phase_filter": phase
            },
            "total_buses_checked": len(bus_voltages)
        }

        metadata = {
            "circuit_name": dss.Circuit.Name(),
            "analysis_type": "voltage_violation_check"
        }

        return format_success_response(data, metadata)

    except ValueError as e:
        return format_error_response(str(e))
    except Exception as e:
        error_msg = f"Error checking voltage violations: {str(e)}"
        logger.exception(error_msg)
        return format_error_response(error_msg)
