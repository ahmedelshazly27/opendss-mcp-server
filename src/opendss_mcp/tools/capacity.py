"""
Feeder capacity analysis module for OpenDSS.

This module provides functions for determining the maximum DER hosting capacity
at a specific bus before constraint violations occur.
"""

import logging
from typing import Any, Dict, List, Optional

import opendssdirect as dss

from ..utils.formatters import format_success_response, format_error_response
from ..utils.validators import validate_positive_float
from .voltage_checker import check_voltage_violations

logger = logging.getLogger(__name__)

# Maximum number of iterations to prevent infinite loops
MAX_ITERATIONS = 1000

# Supported DER types
SUPPORTED_DER_TYPES = ["solar", "battery", "wind"]


def _check_line_loading() -> Dict[str, Any]:
    """Check if any lines exceed 100% loading.

    Returns:
        Dictionary with overloaded lines information:
            - has_overloads: bool
            - overloaded_lines: list of {line: str, loading_pct: float}
            - max_loading_pct: float
    """
    overloaded_lines = []
    max_loading = 0.0

    try:
        # Iterate through all lines
        line_count = dss.Lines.Count()
        if line_count == 0:
            return {
                "has_overloads": False,
                "overloaded_lines": [],
                "max_loading_pct": 0.0,
            }

        dss.Lines.First()
        for _ in range(line_count):
            line_name = dss.Lines.Name()

            # Get line currents and normal ampacity
            dss.Circuit.SetActiveElement(f"Line.{line_name}")
            currents = dss.CktElement.CurrentsMagAng()
            normal_amps = dss.CktElement.NormalAmps()

            if normal_amps > 0 and currents:
                # Get maximum phase current (currents are interleaved mag/angle)
                phase_currents = [currents[i] for i in range(0, len(currents), 2)]
                max_current = max(phase_currents) if phase_currents else 0.0

                # Calculate loading percentage
                loading_pct = (max_current / normal_amps) * 100.0

                if loading_pct > max_loading:
                    max_loading = loading_pct

                if loading_pct > 100.0:
                    overloaded_lines.append(
                        {"line": line_name, "loading_pct": round(loading_pct, 2)}
                    )

            dss.Lines.Next()

    except Exception as e:
        logger.error(f"Error checking line loading: {e}")

    return {
        "has_overloads": len(overloaded_lines) > 0,
        "overloaded_lines": overloaded_lines,
        "max_loading_pct": round(max_loading, 2),
    }


def _add_der(bus_id: str, der_type: str, capacity_kw: float) -> bool:
    """Add a DER to the specified bus.

    Args:
        bus_id: Bus identifier
        der_type: Type of DER ("solar", "battery", "wind")
        capacity_kw: DER capacity in kW

    Returns:
        bool: True if DER was added successfully
    """
    try:
        # Get bus voltage base
        dss.Circuit.SetActiveBus(bus_id)
        kv_base = dss.Bus.kVBase()

        if kv_base == 0:
            logger.error(f"Bus {bus_id} has zero voltage base")
            return False

        # Create unique DER name
        der_name = f"der_test_{bus_id}"

        if der_type == "solar":
            # Add PV system
            dss.Text.Command(
                f"New PVSystem.{der_name} Bus1={bus_id} kV={kv_base} kVA={capacity_kw} Pmpp={capacity_kw} irradiance=1.0"
            )
        elif der_type == "battery":
            # Add storage
            dss.Text.Command(
                f"New Storage.{der_name} Bus1={bus_id} kV={kv_base} kWrated={capacity_kw} kWhrated={capacity_kw * 4} %stored=100 %discharge=100"
            )
        elif der_type == "wind":
            # Add generator (simplified wind model)
            dss.Text.Command(
                f"New Generator.{der_name} Bus1={bus_id} kV={kv_base} kW={capacity_kw} PF=1.0"
            )
        else:
            logger.error(f"Unsupported DER type: {der_type}")
            return False

        return True

    except Exception as e:
        logger.error(f"Error adding DER: {e}")
        return False


def _remove_der(bus_id: str) -> None:
    """Remove test DER from the circuit.

    Args:
        bus_id: Bus identifier
    """
    try:
        der_name = f"der_test_{bus_id}"
        # Try to disable all possible DER types
        for element_type in ["PVSystem", "Storage", "Generator"]:
            try:
                dss.Text.Command(f"{element_type}.{der_name}.enabled=no")
            except:
                pass  # Element might not exist
    except Exception as e:
        logger.error(f"Error removing DER: {e}")


def analyze_feeder_capacity(
    bus_id: str,
    der_type: str = "solar",
    increment_kw: float = 100,
    max_capacity_kw: float = 10000,
    constraints: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Analyze maximum DER hosting capacity at a specific bus.

    This function performs an iterative capacity analysis by incrementally
    adding DER capacity at the specified bus and checking for constraint
    violations (voltage limits and line loading). The analysis stops when
    a violation is detected or the maximum capacity is reached.

    Args:
        bus_id: Identifier of the bus where DER will be connected
        der_type: Type of DER to analyze - "solar", "battery", or "wind" (default: "solar")
        increment_kw: Capacity increment for each iteration in kW (default: 100)
        max_capacity_kw: Maximum capacity to test in kW (default: 10000)
        constraints: Optional dictionary of constraint limits:
            - min_voltage_pu: Minimum voltage limit (default: 0.95)
            - max_voltage_pu: Maximum voltage limit (default: 1.05)
            - max_line_loading_pct: Maximum line loading (default: 100%)

    Returns:
        Dictionary containing:
            - success: Boolean indicating if the operation was successful
            - data: Dictionary with capacity analysis results
            - metadata: Additional metadata about the analysis
            - errors: List of error messages if any occurred

    Example:
        >>> result = analyze_feeder_capacity("675", der_type="solar", increment_kw=100)
        >>> if result['success']:
        ...     max_capacity = result['data']['max_capacity_kw']
        ...     print(f"Maximum capacity: {max_capacity} kW")
    """
    try:
        # Validate inputs
        validate_positive_float(increment_kw, "increment_kw")
        validate_positive_float(max_capacity_kw, "max_capacity_kw")

        if der_type not in SUPPORTED_DER_TYPES:
            return format_error_response(
                f"Unsupported DER type '{der_type}'. Supported types: {', '.join(SUPPORTED_DER_TYPES)}"
            )

        if increment_kw > max_capacity_kw:
            return format_error_response(
                f"increment_kw ({increment_kw}) cannot be greater than max_capacity_kw ({max_capacity_kw})"
            )

        # Check if circuit is loaded
        if not dss.Circuit.Name():
            return format_error_response(
                "No circuit loaded. Please load a feeder first using load_feeder tool."
            )

        # Validate bus exists
        all_buses = [bus.lower() for bus in dss.Circuit.AllBusNames()]
        if bus_id.lower() not in all_buses:
            return format_error_response(
                f"Bus '{bus_id}' not found in circuit. Available buses: {', '.join(all_buses[:5])}..."
            )

        # Parse constraints
        constraints = constraints or {}
        min_voltage_pu = constraints.get("min_voltage_pu", 0.95)
        max_voltage_pu = constraints.get("max_voltage_pu", 1.05)
        max_line_loading_pct = constraints.get("max_line_loading_pct", 100.0)

        # Get baseline (no DER) metrics
        dss.Solution.Solve()
        if not dss.Solution.Converged():
            return format_error_response("Baseline power flow did not converge")

        baseline_voltage_check = check_voltage_violations(
            min_voltage_pu, max_voltage_pu
        )
        baseline_loading = _check_line_loading()

        # Initialize capacity curve data
        capacity_curve: List[Dict[str, Any]] = []
        max_capacity_reached = 0.0
        limiting_constraint = None
        violation_details = None

        # Iterative capacity analysis
        capacity = 0.0
        iteration = 0

        while capacity <= max_capacity_kw and iteration < MAX_ITERATIONS:
            iteration += 1

            # Add DER at current capacity
            if not _add_der(bus_id, der_type, capacity):
                return format_error_response(f"Failed to add DER at bus {bus_id}")

            # Run power flow
            dss.Solution.Solve()

            if not dss.Solution.Converged():
                # Power flow didn't converge - capacity limit reached
                _remove_der(bus_id)
                limiting_constraint = "convergence_failure"
                violation_details = "Power flow solution did not converge"
                break

            # Check voltage violations
            voltage_check = check_voltage_violations(min_voltage_pu, max_voltage_pu)
            has_voltage_violations = (
                voltage_check.get("success", False)
                and voltage_check.get("data", {})
                .get("summary", {})
                .get("total_violations", 0)
                > 0
            )

            # Check line loading
            loading_check = _check_line_loading()
            has_loading_violations = (
                loading_check["has_overloads"]
                or loading_check["max_loading_pct"] > max_line_loading_pct
            )

            # Store iteration data
            iteration_data = {
                "capacity_kw": round(capacity, 2),
                "converged": True,
                "voltage_violations": voltage_check.get("data", {})
                .get("summary", {})
                .get("total_violations", 0),
                "max_line_loading_pct": loading_check["max_loading_pct"],
                "has_violations": has_voltage_violations or has_loading_violations,
            }
            capacity_curve.append(iteration_data)

            # Check for violations
            if has_voltage_violations or has_loading_violations:
                # Violation detected - capacity limit reached
                _remove_der(bus_id)

                if has_voltage_violations:
                    limiting_constraint = "voltage_violation"
                    worst = (
                        voltage_check.get("data", {})
                        .get("summary", {})
                        .get("worst_violation")
                    )
                    if worst:
                        violation_details = f"Voltage violation at bus {worst['bus']} phase {worst['phase']}: {worst['voltage_pu']} pu"
                    else:
                        violation_details = "Voltage limit exceeded"
                else:
                    limiting_constraint = "line_overload"
                    overloaded = loading_check["overloaded_lines"]
                    if overloaded:
                        line_info = overloaded[0]
                        violation_details = f"Line {line_info['line']} overloaded: {line_info['loading_pct']}%"
                    else:
                        violation_details = (
                            f"Line loading exceeded {max_line_loading_pct}%"
                        )

                break

            # No violations - update max capacity and continue
            max_capacity_reached = capacity
            _remove_der(bus_id)
            capacity += increment_kw

        # Remove test DER
        _remove_der(bus_id)

        # Prepare results
        data = {
            "bus_id": bus_id,
            "der_type": der_type,
            "max_capacity_kw": round(max_capacity_reached, 2),
            "limiting_constraint": limiting_constraint,
            "violation_details": violation_details,
            "capacity_curve": capacity_curve,
            "baseline": {
                "voltage_violations": baseline_voltage_check.get("data", {})
                .get("summary", {})
                .get("total_violations", 0),
                "max_line_loading_pct": baseline_loading["max_loading_pct"],
            },
            "constraints": {
                "min_voltage_pu": min_voltage_pu,
                "max_voltage_pu": max_voltage_pu,
                "max_line_loading_pct": max_line_loading_pct,
            },
            "analysis_parameters": {
                "increment_kw": increment_kw,
                "max_capacity_tested_kw": max_capacity_kw,
                "iterations_performed": iteration,
            },
        }

        metadata = {
            "circuit_name": dss.Circuit.Name(),
            "analysis_type": "hosting_capacity",
        }

        return format_success_response(data, metadata)

    except ValueError as e:
        return format_error_response(str(e))
    except Exception as e:
        error_msg = f"Error analyzing feeder capacity: {str(e)}"
        logger.exception(error_msg)
        return format_error_response(error_msg)
