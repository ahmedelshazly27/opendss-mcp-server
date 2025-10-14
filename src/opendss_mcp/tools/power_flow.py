"""
Power flow analysis module for OpenDSS.

This module provides functions for running power flow analysis on OpenDSS circuits,
with optional harmonic analysis capabilities.
"""

import logging
from typing import Any

import opendssdirect as dss

from ..utils.formatters import format_success_response, format_error_response
from ..utils.harmonics import get_harmonic_voltages, get_harmonic_currents

# Map of solution mode names to their corresponding integer values in OpenDSS
SOLUTION_MODES = {
    'snapshot': 0,
    'snap': 0,
    'daily': 1,
    'yearly': 2,
    'dutycycle': 3,
    'direct': 4,
    'montecarlo1': 5,
    'montecarlo2': 6,
    'montecarlo3': 7,
    'faultstudy': 8,
    'mf': 9,
    'peakday': 10,
    'loadduration1': 11,
    'loadduration2': 12
}

logger = logging.getLogger(__name__)


def _perform_harmonic_analysis(all_buses: list[str], harmonic_orders: list[int]) -> dict[str, Any]:
    """Perform harmonic analysis on all buses and lines in the circuit.

    This internal helper function calculates THD for voltages at all buses
    and currents through all lines, and identifies the worst THD location.

    Args:
        all_buses: List of all bus names in the circuit
        harmonic_orders: List of harmonic orders to analyze

    Returns:
        Dictionary containing:
            - thd_voltage: Dictionary mapping bus ID to THD percentage
            - thd_current: Dictionary mapping line ID to THD percentage
            - individual_harmonics: Dictionary of harmonic orders with bus voltages
            - worst_thd_bus: Bus ID with highest voltage THD
            - worst_thd_value: THD percentage at worst bus
    """
    thd_voltage: dict[str, float] = {}
    thd_current: dict[str, float] = {}
    individual_harmonics: dict[int, dict[str, float]] = {}

    # Initialize individual harmonics structure
    for order in harmonic_orders:
        individual_harmonics[order] = {}

    # Calculate THD for all buses
    logger.info(f"Calculating voltage THD for {len(all_buses)} buses...")
    for bus_name in all_buses:
        try:
            result = get_harmonic_voltages(bus_name, harmonic_orders)
            if result.get("success", False):
                # Store THD value
                thd_voltage[bus_name] = result.get("thd_percent", 0.0)

                # Store individual harmonic voltages
                harmonic_voltages = result.get("harmonic_voltages", {})
                for order, data in harmonic_voltages.items():
                    avg_voltage = data.get("avg_voltage_pu", 0.0)
                    individual_harmonics[order][bus_name] = avg_voltage
        except Exception as e:
            logger.warning(f"Error analyzing harmonics for bus {bus_name}: {e}")
            continue

    # Calculate THD for all lines
    all_lines = dss.Lines.AllNames()
    logger.info(f"Calculating current THD for {len(all_lines)} lines...")
    for line_name in all_lines:
        try:
            result = get_harmonic_currents(line_name, harmonic_orders)
            if result.get("success", False):
                thd_current[line_name] = result.get("thd_percent", 0.0)
        except Exception as e:
            logger.warning(f"Error analyzing harmonics for line {line_name}: {e}")
            continue

    # Find worst THD bus
    worst_thd_bus = ""
    worst_thd_value = 0.0

    if thd_voltage:
        worst_thd_bus = max(thd_voltage, key=thd_voltage.get)
        worst_thd_value = thd_voltage[worst_thd_bus]

    logger.info(f"Harmonic analysis complete. Worst THD: {worst_thd_value:.2f}% at bus {worst_thd_bus}")

    return {
        "thd_voltage": thd_voltage,
        "thd_current": thd_current,
        "individual_harmonics": individual_harmonics,
        "worst_thd_bus": worst_thd_bus,
        "worst_thd_value": round(worst_thd_value, 4)
    }


def run_power_flow(
    feeder_id: str,
    options: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Run power flow analysis on a loaded feeder with optional harmonic analysis.

    Args:
        feeder_id: Identifier of the IEEE test feeder (e.g., 'IEEE13')
        options: Dictionary of power flow options
            - max_iterations: Maximum number of iterations (default: 100)
            - tolerance: Convergence tolerance (default: 0.0001)
            - control_mode: Control mode for the solution (default: 'snapshot')
            - harmonic_analysis: Enable harmonic analysis (default: False)
            - harmonic_orders: List of harmonic orders to analyze (default: [1, 3, 5, 7, 9, 11, 13])

    Returns:
        Dictionary containing power flow results and metadata:
            - success: Boolean indicating if operation was successful
            - data: Dictionary with power flow results:
                - feeder_id: The feeder identifier
                - converged: Boolean indicating convergence
                - iterations: Number of iterations performed
                - bus_voltages: Dictionary of bus voltages in per-unit
                - min_voltage: Minimum voltage across all buses
                - max_voltage: Maximum voltage across all buses
                - options: The options used for the analysis
                - harmonics: (Optional) Harmonic analysis results if enabled:
                    - thd_voltage: Dictionary mapping bus ID to THD percentage
                    - thd_current: Dictionary mapping line ID to THD percentage
                    - individual_harmonics: Dictionary of harmonic orders with bus voltages
                    - worst_thd_bus: Bus ID with highest voltage THD
                    - worst_thd_value: THD percentage at worst bus
            - metadata: Additional metadata
            - errors: List of error messages if any occurred

    Example:
        >>> # Basic power flow
        >>> result = run_power_flow("IEEE13")
        >>>
        >>> # Power flow with harmonic analysis
        >>> result = run_power_flow("IEEE13", {
        ...     "harmonic_analysis": True,
        ...     "harmonic_orders": [1, 3, 5, 7, 9, 11, 13]
        ... })
        >>> if result['success']:
        ...     harmonics = result['data']['harmonics']
        ...     print(f"Worst THD: {harmonics['worst_thd_value']:.2f}% at bus {harmonics['worst_thd_bus']}")

    Note:
        - Harmonic analysis is optional and disabled by default for backward compatibility
        - Harmonic analysis requires harmonic sources to be defined in the circuit
        - Harmonic analysis may significantly increase computation time
    """
    try:
        # Set default options if not provided
        options = options or {}
        max_iterations = options.get('max_iterations', 100)
        tolerance = options.get('tolerance', 0.0001)
        control_mode = options.get('control_mode', 'snapshot')
        harmonic_analysis = options.get('harmonic_analysis', False)
        harmonic_orders = options.get('harmonic_orders', [1, 3, 5, 7, 9, 11, 13])

        # Configure power flow settings
        dss.Solution.MaxControlIterations(max_iterations)
        dss.Solution.MaxIterations(max_iterations)

        # Set solution mode (convert string to integer)
        mode_value = SOLUTION_MODES.get(control_mode.lower(), 0)
        dss.Solution.Mode(mode_value)
        # Note: Using default tolerance as it's not configurable in this API

        # Solve the power flow
        dss.Solution.Solve()

        # Check if the solution converged
        converged = dss.Solution.Converged()
        iterations = dss.Solution.Iterations()

        if not converged:
            return format_error_response("Power flow did not converge")

        # Get bus voltages
        bus_voltages = {}
        all_buses = dss.Circuit.AllBusNames()
        for bus_name in all_buses:
            dss.Circuit.SetActiveBus(bus_name)
            voltages = dss.Bus.puVmagAngle()
            # Take the magnitude of the first phase voltage (simplified)
            if voltages and len(voltages) > 0:
                bus_voltages[bus_name.lower()] = voltages[0]

        # Calculate min/max voltages
        if bus_voltages:
            min_voltage = min(bus_voltages.values())
            max_voltage = max(bus_voltages.values())
        else:
            min_voltage = max_voltage = 0.0

        # Prepare base results
        result = {
            'feeder_id': feeder_id,
            'converged': converged,
            'iterations': iterations,
            'bus_voltages': bus_voltages,
            'min_voltage': min_voltage,
            'max_voltage': max_voltage,
            'options': {
                'max_iterations': max_iterations,
                'tolerance': tolerance,
                'control_mode': control_mode
            }
        }

        # Perform harmonic analysis if requested
        if harmonic_analysis:
            logger.info("Running harmonic analysis...")
            harmonics_data = _perform_harmonic_analysis(all_buses, harmonic_orders)
            result['harmonics'] = harmonics_data
            result['options']['harmonic_analysis'] = True
            result['options']['harmonic_orders'] = harmonic_orders

        return format_success_response(result)

    except Exception as e:
        error_msg = f"Error running power flow: {str(e)}"
        logger.exception(error_msg)
        return format_error_response(error_msg)
