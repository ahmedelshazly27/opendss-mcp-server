"""
Power flow analysis module for OpenDSS.

This module provides functions for running power flow analysis on OpenDSS circuits.
"""

import logging
from typing import Any, Dict, Optional

import opendssdirect as dss

from ..utils.formatters import format_success_response, format_error_response

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

def run_power_flow(
    feeder_id: str,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run power flow analysis on a loaded feeder.

    Args:
        feeder_id: Identifier of the IEEE test feeder (e.g., 'IEEE13')
        options: Dictionary of power flow options
            - max_iterations: Maximum number of iterations (default: 100)
            - tolerance: Convergence tolerance (default: 0.0001)
            - control_mode: Control mode for the solution (default: 'snapshot')

    Returns:
        Dictionary containing power flow results and metadata
    """
    try:
        # Set default options if not provided
        options = options or {}
        max_iterations = options.get('max_iterations', 100)
        tolerance = options.get('tolerance', 0.0001)
        control_mode = options.get('control_mode', 'snapshot')

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

        # Prepare results
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

        return format_success_response(result)

    except Exception as e:
        error_msg = f"Error running power flow: {str(e)}"
        logger.exception(error_msg)
        return format_error_response(error_msg)
