"""
Harmonic analysis utilities for OpenDSS.

This module provides functions for performing frequency scans, calculating
total harmonic distortion (THD), and extracting harmonic voltage and current
magnitudes at specific buses and lines in the power system.
"""

import logging
import math
from typing import Any

import opendssdirect as dss

logger = logging.getLogger(__name__)


def run_frequency_scan(orders: list[int] | None = None) -> dict[str, Any]:
    """Run frequency scan to analyze harmonic content in the circuit.

    This function configures OpenDSS to run a harmonic frequency scan at
    specified harmonic orders. The scan analyzes the system response at
    each harmonic frequency (order * fundamental frequency).

    Args:
        orders: List of harmonic orders to scan (e.g., [3, 5, 7, 9, 11, 13]).
                Default is [3, 5, 7, 9, 11, 13] if not specified.
                Order 1 represents the fundamental frequency (60 Hz).

    Returns:
        Dictionary containing:
            - success: Boolean indicating if the scan was successful
            - harmonic_data: Dictionary mapping harmonic order to results:
                - order: Harmonic order number
                - frequency_hz: Frequency in Hz (order * 60)
                - converged: Boolean indicating if solution converged
            - fundamental_frequency_hz: Fundamental frequency (typically 60 Hz)
            - errors: List of error messages if any occurred

    Example:
        >>> result = run_frequency_scan([3, 5, 7])
        >>> if result['success']:
        ...     for order, data in result['harmonic_data'].items():
        ...         print(f"Order {order}: {data['frequency_hz']} Hz")

    Note:
        - The circuit must be loaded before running the frequency scan
        - OpenDSS must be configured with harmonic sources for meaningful results
        - Solution mode is temporarily changed to "Harmonic" during the scan
        - Original solution mode is restored after the scan completes
    """
    if orders is None:
        orders = [3, 5, 7, 9, 11, 13]

    try:
        # Check if circuit is loaded
        if not dss.Circuit.Name():
            return {
                "success": False,
                "harmonic_data": {},
                "fundamental_frequency_hz": 60.0,
                "errors": ["No circuit loaded. Please load a feeder first."]
            }

        # Get fundamental frequency
        fundamental_freq = dss.Solution.Frequency()
        if fundamental_freq == 0:
            fundamental_freq = 60.0  # Default to 60 Hz

        # Store original solution mode
        original_mode = dss.Solution.Mode()

        # Set solution mode to Harmonic using Text command
        dss.Text.Command("Set Mode=Harmonic")

        harmonic_data: dict[int, dict[str, Any]] = {}
        errors: list[str] = []

        # Run scan for each harmonic order
        for order in orders:
            try:
                # Set harmonic order using Text command
                dss.Text.Command(f"Set Harmonic={order}")

                # Calculate frequency for this order
                frequency_hz = order * fundamental_freq

                # Solve circuit at this frequency
                dss.Text.Command("Solve")

                # Check convergence
                converged = dss.Solution.Converged()

                harmonic_data[order] = {
                    "order": order,
                    "frequency_hz": round(frequency_hz, 2),
                    "converged": converged
                }

                if not converged:
                    logger.warning(f"Harmonic scan did not converge at order {order}")
                    errors.append(f"Solution did not converge at harmonic order {order}")

            except Exception as e:
                error_msg = f"Error scanning harmonic order {order}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Restore original solution mode
        try:
            dss.Solution.Mode(original_mode)
        except Exception as e:
            logger.warning(f"Could not restore original solution mode: {e}")

        success = len(harmonic_data) > 0

        return {
            "success": success,
            "harmonic_data": harmonic_data,
            "fundamental_frequency_hz": fundamental_freq,
            "errors": errors if errors else []
        }

    except Exception as e:
        error_msg = f"Error running frequency scan: {str(e)}"
        logger.exception(error_msg)
        return {
            "success": False,
            "harmonic_data": {},
            "fundamental_frequency_hz": 60.0,
            "errors": [error_msg]
        }


def calculate_thd(harmonics: dict[int, float]) -> float:
    """Calculate Total Harmonic Distortion (THD) from harmonic magnitudes.

    THD is calculated using the IEEE standard formula:
    THD = sqrt(sum(H_n^2 for n > 1)) / H_1 * 100

    Where:
        - H_n is the magnitude of the nth harmonic
        - H_1 is the fundamental (first harmonic) magnitude
        - n > 1 represents all harmonics above the fundamental

    Args:
        harmonics: Dictionary mapping harmonic order (int) to magnitude (float).
                   Must include order 1 (fundamental) for valid calculation.

    Returns:
        THD percentage as a float. Returns 0.0 if:
            - Fundamental (order 1) is missing or zero
            - No harmonics above order 1 are present
            - Dictionary is empty

    Example:
        >>> harmonics = {1: 120.0, 3: 10.0, 5: 8.0, 7: 5.0}
        >>> thd = calculate_thd(harmonics)
        >>> print(f"THD: {thd:.2f}%")
        THD: 11.18%

    Note:
        - Input magnitudes should be in the same units (V for voltage, A for current)
        - THD is typically expressed as a percentage
        - Higher THD indicates more distortion from the fundamental waveform
    """
    try:
        # Get fundamental magnitude
        if 1 not in harmonics or harmonics[1] == 0:
            logger.warning("Fundamental harmonic (order 1) is missing or zero")
            return 0.0

        fundamental = harmonics[1]

        # Calculate sum of squares for harmonics above fundamental
        sum_of_squares = 0.0
        harmonic_count = 0

        for order, magnitude in harmonics.items():
            if order > 1:  # Only include harmonics above fundamental
                sum_of_squares += magnitude ** 2
                harmonic_count += 1

        # Check if we have any harmonics
        if harmonic_count == 0:
            logger.warning("No harmonics above fundamental found")
            return 0.0

        # Calculate THD percentage
        thd = (math.sqrt(sum_of_squares) / fundamental) * 100.0

        return round(thd, 4)

    except Exception as e:
        logger.error(f"Error calculating THD: {e}")
        return 0.0


def get_harmonic_voltages(bus_id: str, orders: list[int] | None = None) -> dict[str, Any]:
    """Get voltage magnitudes at each harmonic order for a specific bus.

    This function runs a frequency scan and extracts voltage magnitudes
    at the specified bus for each harmonic order. Results include per-phase
    voltages and calculated THD.

    Args:
        bus_id: Identifier of the bus to analyze
        orders: List of harmonic orders to analyze (e.g., [1, 3, 5, 7, 9, 11, 13]).
                Default is [1, 3, 5, 7, 9, 11, 13] if not specified.
                Order 1 (fundamental) is required for THD calculation.

    Returns:
        Dictionary containing:
            - success: Boolean indicating if the operation was successful
            - bus_id: The bus identifier
            - harmonic_voltages: Dictionary mapping order to voltage data:
                - order: Harmonic order
                - frequency_hz: Frequency in Hz
                - voltages_pu: List of per-unit voltages for each phase
                - avg_voltage_pu: Average voltage across phases
            - thd_percent: Total harmonic distortion percentage
            - fundamental_voltage_pu: Fundamental voltage magnitude
            - errors: List of error messages if any occurred

    Example:
        >>> result = get_harmonic_voltages("675", [1, 3, 5, 7])
        >>> if result['success']:
        ...     print(f"Bus {result['bus_id']}")
        ...     print(f"THD: {result['thd_percent']:.2f}%")
        ...     for order, data in result['harmonic_voltages'].items():
        ...         print(f"  Order {order}: {data['avg_voltage_pu']:.4f} pu")

    Note:
        - The circuit must be loaded and solved before calling this function
        - Bus ID must exist in the loaded circuit
        - Harmonic sources must be present for meaningful harmonic analysis
    """
    if orders is None:
        orders = [1, 3, 5, 7, 9, 11, 13]

    try:
        # Check if circuit is loaded
        if not dss.Circuit.Name():
            return {
                "success": False,
                "bus_id": bus_id,
                "harmonic_voltages": {},
                "thd_percent": 0.0,
                "fundamental_voltage_pu": 0.0,
                "errors": ["No circuit loaded. Please load a feeder first."]
            }

        # Validate bus exists
        all_buses = [bus.lower() for bus in dss.Circuit.AllBusNames()]
        if bus_id.lower() not in all_buses:
            return {
                "success": False,
                "bus_id": bus_id,
                "harmonic_voltages": {},
                "thd_percent": 0.0,
                "fundamental_voltage_pu": 0.0,
                "errors": [f"Bus '{bus_id}' not found in circuit"]
            }

        # Store original solution mode
        original_mode = dss.Solution.Mode()

        # Get fundamental frequency
        fundamental_freq = dss.Solution.Frequency()
        if fundamental_freq == 0:
            fundamental_freq = 60.0

        harmonic_voltages: dict[int, dict[str, Any]] = {}
        errors: list[str] = []
        thd_magnitudes: dict[int, float] = {}

        # Set solution mode to Harmonic using Text command
        dss.Text.Command("Set Mode=Harmonic")

        # Scan each harmonic order
        for order in orders:
            try:
                # Set harmonic order and solve using Text commands
                dss.Text.Command(f"Set Harmonic={order}")
                frequency_hz = order * fundamental_freq
                dss.Text.Command("Solve")

                if not dss.Solution.Converged():
                    logger.warning(f"Solution did not converge at order {order}")
                    errors.append(f"Solution did not converge at harmonic order {order}")
                    continue

                # Get voltages at the bus
                dss.Circuit.SetActiveBus(bus_id)
                voltages_pu = dss.Bus.puVmagAngle()[::2]  # Get magnitudes only (every other value)

                if not voltages_pu:
                    logger.warning(f"No voltage data available for bus {bus_id} at order {order}")
                    continue

                # Calculate average voltage across phases
                avg_voltage = sum(voltages_pu) / len(voltages_pu)

                harmonic_voltages[order] = {
                    "order": order,
                    "frequency_hz": round(frequency_hz, 2),
                    "voltages_pu": [round(v, 6) for v in voltages_pu],
                    "avg_voltage_pu": round(avg_voltage, 6)
                }

                # Store for THD calculation
                thd_magnitudes[order] = avg_voltage

            except Exception as e:
                error_msg = f"Error getting voltages at order {order}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Restore original solution mode
        try:
            dss.Solution.Mode(original_mode)
        except Exception as e:
            logger.warning(f"Could not restore original solution mode: {e}")

        # Calculate THD
        thd_percent = calculate_thd(thd_magnitudes)

        # Get fundamental voltage
        fundamental_voltage = thd_magnitudes.get(1, 0.0)

        success = len(harmonic_voltages) > 0

        return {
            "success": success,
            "bus_id": bus_id,
            "harmonic_voltages": harmonic_voltages,
            "thd_percent": thd_percent,
            "fundamental_voltage_pu": fundamental_voltage,
            "errors": errors if errors else []
        }

    except Exception as e:
        error_msg = f"Error getting harmonic voltages: {str(e)}"
        logger.exception(error_msg)
        return {
            "success": False,
            "bus_id": bus_id,
            "harmonic_voltages": {},
            "thd_percent": 0.0,
            "fundamental_voltage_pu": 0.0,
            "errors": [error_msg]
        }


def get_harmonic_currents(line_id: str, orders: list[int] | None = None) -> dict[str, Any]:
    """Get current magnitudes at each harmonic order for a specific line.

    This function runs a frequency scan and extracts current magnitudes
    flowing through the specified line for each harmonic order. Results include
    per-phase currents and calculated THD.

    Args:
        line_id: Identifier of the line to analyze
        orders: List of harmonic orders to analyze (e.g., [1, 3, 5, 7, 9, 11, 13]).
                Default is [1, 3, 5, 7, 9, 11, 13] if not specified.
                Order 1 (fundamental) is required for THD calculation.

    Returns:
        Dictionary containing:
            - success: Boolean indicating if the operation was successful
            - line_id: The line identifier
            - harmonic_currents: Dictionary mapping order to current data:
                - order: Harmonic order
                - frequency_hz: Frequency in Hz
                - currents_amps: List of current magnitudes for each phase
                - max_current_amps: Maximum current across phases
            - thd_percent: Total harmonic distortion percentage
            - fundamental_current_amps: Fundamental current magnitude
            - errors: List of error messages if any occurred

    Example:
        >>> result = get_harmonic_currents("Line.650632", [1, 3, 5, 7])
        >>> if result['success']:
        ...     print(f"Line {result['line_id']}")
        ...     print(f"THD: {result['thd_percent']:.2f}%")
        ...     for order, data in result['harmonic_currents'].items():
        ...         print(f"  Order {order}: {data['max_current_amps']:.2f} A")

    Note:
        - The circuit must be loaded and solved before calling this function
        - Line ID must exist in the loaded circuit
        - Harmonic sources must be present for meaningful harmonic analysis
        - Line ID can be specified with or without "Line." prefix
    """
    if orders is None:
        orders = [1, 3, 5, 7, 9, 11, 13]

    try:
        # Check if circuit is loaded
        if not dss.Circuit.Name():
            return {
                "success": False,
                "line_id": line_id,
                "harmonic_currents": {},
                "thd_percent": 0.0,
                "fundamental_current_amps": 0.0,
                "errors": ["No circuit loaded. Please load a feeder first."]
            }

        # Validate line exists (handle "Line." prefix)
        line_name = line_id.replace("Line.", "").replace("line.", "")
        all_lines = [line.lower() for line in dss.Lines.AllNames()]

        if line_name.lower() not in all_lines:
            return {
                "success": False,
                "line_id": line_id,
                "harmonic_currents": {},
                "thd_percent": 0.0,
                "fundamental_current_amps": 0.0,
                "errors": [f"Line '{line_id}' not found in circuit"]
            }

        # Store original solution mode
        original_mode = dss.Solution.Mode()

        # Get fundamental frequency
        fundamental_freq = dss.Solution.Frequency()
        if fundamental_freq == 0:
            fundamental_freq = 60.0

        harmonic_currents: dict[int, dict[str, Any]] = {}
        errors: list[str] = []
        thd_magnitudes: dict[int, float] = {}

        # Set solution mode to Harmonic using Text command
        dss.Text.Command("Set Mode=Harmonic")

        # Scan each harmonic order
        for order in orders:
            try:
                # Set harmonic order and solve using Text commands
                dss.Text.Command(f"Set Harmonic={order}")
                frequency_hz = order * fundamental_freq
                dss.Text.Command("Solve")

                if not dss.Solution.Converged():
                    logger.warning(f"Solution did not converge at order {order}")
                    errors.append(f"Solution did not converge at harmonic order {order}")
                    continue

                # Get currents through the line
                dss.Circuit.SetActiveElement(f"Line.{line_name}")
                currents_mag_ang = dss.CktElement.CurrentsMagAng()

                if not currents_mag_ang:
                    logger.warning(f"No current data available for line {line_id} at order {order}")
                    continue

                # Extract magnitudes only (every other value in the interleaved mag/angle array)
                currents_amps = [currents_mag_ang[i] for i in range(0, len(currents_mag_ang), 2)]

                if not currents_amps:
                    continue

                # Get maximum current across phases
                max_current = max(currents_amps)

                harmonic_currents[order] = {
                    "order": order,
                    "frequency_hz": round(frequency_hz, 2),
                    "currents_amps": [round(c, 4) for c in currents_amps],
                    "max_current_amps": round(max_current, 4)
                }

                # Store for THD calculation (use max current)
                thd_magnitudes[order] = max_current

            except Exception as e:
                error_msg = f"Error getting currents at order {order}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Restore original solution mode
        try:
            dss.Solution.Mode(original_mode)
        except Exception as e:
            logger.warning(f"Could not restore original solution mode: {e}")

        # Calculate THD
        thd_percent = calculate_thd(thd_magnitudes)

        # Get fundamental current
        fundamental_current = thd_magnitudes.get(1, 0.0)

        success = len(harmonic_currents) > 0

        return {
            "success": success,
            "line_id": line_id,
            "harmonic_currents": harmonic_currents,
            "thd_percent": thd_percent,
            "fundamental_current_amps": fundamental_current,
            "errors": errors if errors else []
        }

    except Exception as e:
        error_msg = f"Error getting harmonic currents: {str(e)}"
        logger.exception(error_msg)
        return {
            "success": False,
            "line_id": line_id,
            "harmonic_currents": {},
            "thd_percent": 0.0,
            "fundamental_current_amps": 0.0,
            "errors": [error_msg]
        }
