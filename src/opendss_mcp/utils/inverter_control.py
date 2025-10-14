"""
Inverter control utilities for OpenDSS.

This module provides functions for configuring smart inverter control modes
including volt-var and volt-watt control for distributed energy resources (DER).
"""

import json
import logging
from pathlib import Path
from typing import Any

import opendssdirect as dss

logger = logging.getLogger(__name__)

# Directory containing standard control curves
CURVES_DIR = Path(__file__).parent.parent / "data" / "control_curves"

# Mapping of standard curve names to JSON files
STANDARD_CURVES = {
    "IEEE1547": "ieee1547.json",
    "RULE21": "rule21.json",
}


def load_curve(curve_name: str) -> list[tuple[float, float]]:
    """Load control curve points from a JSON file.

    This function loads volt-var or volt-watt curve definitions from JSON files.
    It supports standard curves (IEEE1547, RULE21) by name or custom curves by
    file path.

    Args:
        curve_name: Name of standard curve ("IEEE1547", "RULE21") or path to
                    a custom JSON file. Curve names are case-insensitive.

    Returns:
        List of (x, y) tuples representing curve points where:
        - For volt-var: (voltage_pu, var_pu)
        - For volt-watt: (voltage_pu, watt_pu)

    Raises:
        FileNotFoundError: If the specified curve file doesn't exist
        ValueError: If the JSON file is invalid or missing required fields
        KeyError: If the curve name is not recognized

    Example:
        >>> # Load standard IEEE 1547 curve
        >>> points = load_curve("IEEE1547")
        >>> print(points)
        [(0.92, 0.44), (0.98, 0.0), (1.02, 0.0), (1.08, -0.44)]
        >>>
        >>> # Load custom curve by path
        >>> points = load_curve("path/to/my_custom_curve.json")
        >>>
        >>> # Use curve points in configuration
        >>> configure_volt_var_control("PV1", points)

    Note:
        - Standard curves are located in src/opendss_mcp/data/control_curves/
        - Custom curve files must follow the JSON format defined in README.md
        - Curve points are returned as-is from the JSON file (no validation)
    """
    try:
        # Check if it's a standard curve name
        curve_upper = curve_name.upper()
        if curve_upper in STANDARD_CURVES:
            curve_file = CURVES_DIR / STANDARD_CURVES[curve_upper]
            logger.info(f"Loading standard curve: {curve_upper}")
        else:
            # Treat as file path
            curve_file = Path(curve_name)
            logger.info(f"Loading custom curve from: {curve_file}")

        # Check if file exists
        if not curve_file.exists():
            available = ", ".join(STANDARD_CURVES.keys())
            raise FileNotFoundError(
                f"Curve file not found: {curve_file}\n"
                f"Available standard curves: {available}\n"
                f"Or provide a valid path to a custom JSON file."
            )

        # Load and parse JSON
        with open(curve_file, "r") as f:
            data = json.load(f)

        # Validate required fields
        if "points" not in data:
            raise ValueError(
                f"Invalid curve file {curve_file}: missing 'points' field"
            )

        # Extract points and convert to tuples
        points = [tuple(point) for point in data["points"]]

        if len(points) < 2:
            raise ValueError(
                f"Invalid curve {curve_file}: must have at least 2 points"
            )

        logger.info(
            f"Loaded curve '{data.get('name', 'unknown')}' with {len(points)} points"
        )
        return points

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in curve file {curve_name}: {e}")
    except Exception as e:
        logger.error(f"Error loading curve {curve_name}: {e}")
        raise


def configure_volt_var_control(
    pv_name: str,
    curve_points: list[tuple[float, float]],
    response_time: float = 10.0,
    curve_name: str | None = None
) -> None:
    """Configure volt-var control for a PV system or inverter in OpenDSS.

    This function creates the necessary OpenDSS objects (XYCurve and InvControl)
    to enable autonomous volt-var control on a PVSystem element. The inverter
    will automatically adjust reactive power output based on local voltage
    according to the specified curve.

    OpenDSS Commands Executed:
        1. New XYCurve: Defines the voltage-var relationship
           - npts: Number of points in the curve
           - xarray: Voltage values in per-unit
           - yarray: Reactive power values in per-unit

        2. New InvControl: Smart inverter controller
           - PVSystemList: Which PV system(s) to control
           - Mode: VOLTVAR (reactive power control based on voltage)
           - voltage_curvex_ref: XYCurve name for volt-var function
           - AvgWindowLen: Averaging window for voltage measurements
           - DeltaQ_Factor: Response time / ramp rate for var changes
           - RefReactivePower: Reference point (VARAVAL = available vars)

    Args:
        pv_name: Name of the PVSystem element to control (without "PVSystem." prefix)
        curve_points: List of (voltage_pu, var_pu) tuples defining the curve.
                      Voltage in per-unit, vars in per-unit of inverter kVA rating.
        response_time: Response time in seconds for reactive power changes (default: 10.0).
                       Smaller values = faster response, larger = slower/smoother.
        curve_name: Optional name for the XYCurve. If None, auto-generated from pv_name.

    Returns:
        None

    Example:
        >>> # Load IEEE 1547 curve and apply to a PV system
        >>> curve = load_curve("IEEE1547")
        >>> configure_volt_var_control("PV_675", curve, response_time=5.0)
        >>>
        >>> # After configuration, run power flow to see volt-var in action
        >>> dss.Text.Command("Solve")
        >>>
        >>> # Custom curve for specific voltage support
        >>> custom_curve = [(0.95, 0.44), (0.98, 0.0), (1.02, 0.0), (1.05, -0.44)]
        >>> configure_volt_var_control("PV_611", custom_curve)

    Note:
        - PVSystem must already exist in the circuit
        - Curve points should be sorted by voltage (ascending)
        - Positive vars = absorb (inductive), negative = inject (capacitive)
        - Response time affects how quickly the inverter adjusts to voltage changes
        - The InvControl object updates every OpenDSS control iteration
    """
    try:
        # Generate curve name if not provided
        if curve_name is None:
            curve_name = f"vv_{pv_name}"

        # Validate curve points
        if len(curve_points) < 2:
            raise ValueError("Curve must have at least 2 points")

        # Extract x and y arrays
        x_values = [point[0] for point in curve_points]
        y_values = [point[1] for point in curve_points]

        # Check if x values are sorted
        if x_values != sorted(x_values):
            logger.warning(f"Curve points for {pv_name} are not sorted by voltage")

        # Format arrays for OpenDSS
        x_array_str = "[" + ", ".join(f"{x:.6f}" for x in x_values) + "]"
        y_array_str = "[" + ", ".join(f"{y:.6f}" for y in y_values) + "]"

        # Create XYCurve object
        logger.info(f"Creating XYCurve '{curve_name}' with {len(curve_points)} points")
        dss.Text.Command(
            f"New XYCurve.{curve_name} "
            f"npts={len(curve_points)} "
            f"xarray={x_array_str} "
            f"yarray={y_array_str}"
        )

        # Create InvControl object
        inv_control_name = f"InvCtrl_{pv_name}"
        logger.info(f"Creating InvControl '{inv_control_name}' for PVSystem '{pv_name}'")

        # Calculate DeltaQ_Factor from response time
        # DeltaQ_Factor controls the ramp rate: deltaQ = DeltaQ_Factor * (Qdesired - Qcurrent)
        # Typical range: 0.1 (slow) to 1.0 (fast)
        delta_q_factor = min(1.0, max(0.01, 1.0 / response_time))

        # Note: InvControl parameter names differ from DSS documentation
        # Using 'vvc_curve1' instead of 'voltage_curvex_ref' for volt-var
        dss.Text.Command(
            f"New InvControl.{inv_control_name} "
            f"PVSystemList=[{pv_name}] "
            f"Mode=VOLTVAR "
            f"vvc_curve1={curve_name} "
            f"AvgWindowLen=1 "
            f"DeltaQ_Factor={delta_q_factor:.4f} "
            f"RefReactivePower=VARAVAL"
        )

        logger.info(
            f"Volt-var control configured for {pv_name} "
            f"(curve: {curve_name}, response: {response_time}s)"
        )

    except Exception as e:
        error_msg = f"Error configuring volt-var control for {pv_name}: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def configure_volt_watt_control(
    pv_name: str,
    curve_points: list[tuple[float, float]],
    curve_name: str | None = None
) -> None:
    """Configure volt-watt control for a PV system or inverter in OpenDSS.

    This function creates the necessary OpenDSS objects (XYCurve and InvControl)
    to enable volt-watt curtailment control. The inverter will automatically
    reduce real power output when voltage exceeds specified thresholds, helping
    prevent overvoltage conditions.

    OpenDSS Commands Executed:
        1. New XYCurve: Defines the voltage-watt relationship
           - npts: Number of points in the curve
           - xarray: Voltage values in per-unit
           - yarray: Power output values in per-unit (of rated)

        2. New InvControl: Smart inverter controller
           - PVSystemList: Which PV system(s) to control
           - Mode: VOLTWATT (real power curtailment based on voltage)
           - voltage_curvex_ref: XYCurve name for volt-watt function
           - AvgWindowLen: Averaging window for voltage measurements

    Args:
        pv_name: Name of the PVSystem element to control (without "PVSystem." prefix)
        curve_points: List of (voltage_pu, watt_pu) tuples defining the curve.
                      Voltage in per-unit, watts in per-unit of rated power (0.0-1.0).
        curve_name: Optional name for the XYCurve. If None, auto-generated from pv_name.

    Returns:
        None

    Example:
        >>> # Typical volt-watt curve: curtail when voltage > 1.06 pu
        >>> vw_curve = [
        ...     (0.00, 1.00),  # Normal operation below 1.06 pu
        ...     (1.06, 1.00),  # Start curtailment
        ...     (1.10, 0.20)   # 80% curtailment at 1.10 pu
        ... ]
        >>> configure_volt_watt_control("PV_675", vw_curve)
        >>>
        >>> # Aggressive curtailment for high-voltage areas
        >>> aggressive_curve = [(0.0, 1.0), (1.05, 1.0), (1.08, 0.0)]
        >>> configure_volt_watt_control("PV_611", aggressive_curve)

    Note:
        - PVSystem must already exist in the circuit
        - Curve points should be sorted by voltage (ascending)
        - Watt values are per-unit: 1.0 = full power, 0.0 = fully curtailed
        - Volt-watt is typically used for overvoltage prevention
        - Standard range: curtail above 1.06-1.10 pu (per IEEE 1547-2018)
        - Can be combined with volt-var (requires separate InvControl objects)
    """
    try:
        # Generate curve name if not provided
        if curve_name is None:
            curve_name = f"vw_{pv_name}"

        # Validate curve points
        if len(curve_points) < 2:
            raise ValueError("Curve must have at least 2 points")

        # Extract x and y arrays
        x_values = [point[0] for point in curve_points]
        y_values = [point[1] for point in curve_points]

        # Check if x values are sorted
        if x_values != sorted(x_values):
            logger.warning(f"Curve points for {pv_name} are not sorted by voltage")

        # Validate watt values (should be 0.0 to 1.0)
        for y in y_values:
            if y < 0.0 or y > 1.0:
                logger.warning(
                    f"Watt value {y} outside typical range [0.0, 1.0] for {pv_name}"
                )

        # Format arrays for OpenDSS
        x_array_str = "[" + ", ".join(f"{x:.6f}" for x in x_values) + "]"
        y_array_str = "[" + ", ".join(f"{y:.6f}" for y in y_values) + "]"

        # Create XYCurve object
        logger.info(f"Creating XYCurve '{curve_name}' with {len(curve_points)} points")
        dss.Text.Command(
            f"New XYCurve.{curve_name} "
            f"npts={len(curve_points)} "
            f"xarray={x_array_str} "
            f"yarray={y_array_str}"
        )

        # Create InvControl object
        inv_control_name = f"InvCtrl_{pv_name}"
        logger.info(f"Creating InvControl '{inv_control_name}' for PVSystem '{pv_name}'")

        # Note: InvControl parameter names differ from DSS documentation
        # Using 'voltwatt_curve' for volt-watt mode
        dss.Text.Command(
            f"New InvControl.{inv_control_name} "
            f"PVSystemList=[{pv_name}] "
            f"Mode=VOLTWATT "
            f"voltwatt_curve={curve_name} "
            f"AvgWindowLen=1"
        )

        logger.info(
            f"Volt-watt control configured for {pv_name} (curve: {curve_name})"
        )

    except Exception as e:
        error_msg = f"Error configuring volt-watt control for {pv_name}: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def get_inverter_status(pv_name: str) -> dict[str, Any]:
    """Get current status of a PVSystem inverter including control outputs.

    This function retrieves the current operating state of a PVSystem element,
    including real and reactive power output, voltage, and power factor.

    Args:
        pv_name: Name of the PVSystem element (without "PVSystem." prefix)

    Returns:
        Dictionary containing:
            - success: Boolean indicating if status was retrieved
            - pv_name: The PVSystem name
            - kw: Real power output in kW
            - kvar: Reactive power output in kvar
            - kva: Apparent power in kVA
            - pf: Power factor
            - voltage_pu: Terminal voltage in per-unit
            - errors: List of error messages if any

    Example:
        >>> status = get_inverter_status("PV_675")
        >>> if status["success"]:
        ...     print(f"PV Output: {status['kw']:.2f} kW, {status['kvar']:.2f} kvar")
        ...     print(f"Voltage: {status['voltage_pu']:.4f} pu, PF: {status['pf']:.3f}")

    Note:
        - Requires a solved power flow (call dss.Solution.Solve() first)
        - Returns zeros if PVSystem is not found or circuit not solved
    """
    try:
        # Set active element
        element_name = f"PVSystem.{pv_name}"
        result = dss.Circuit.SetActiveElement(element_name)

        if result < 0:
            return {
                "success": False,
                "pv_name": pv_name,
                "kw": 0.0,
                "kvar": 0.0,
                "kva": 0.0,
                "pf": 0.0,
                "voltage_pu": 0.0,
                "errors": [f"PVSystem '{pv_name}' not found in circuit"]
            }

        # Get power output
        powers = dss.CktElement.Powers()
        if len(powers) >= 2:
            # Powers array format: [P1, Q1, P2, Q2, ...] for each terminal
            # Sum the phases (typically first terminal for PV)
            kw = sum(powers[i] for i in range(0, len(powers), 2))
            kvar = sum(powers[i] for i in range(1, len(powers), 2))
        else:
            kw = 0.0
            kvar = 0.0

        # Calculate kVA and power factor
        kva = (kw**2 + kvar**2)**0.5 if (kw != 0 or kvar != 0) else 0.0
        pf = abs(kw / kva) if kva > 0 else 1.0

        # Get terminal voltage
        bus_name = dss.CktElement.BusNames()[0].split(".")[0]  # Get bus name without phase
        dss.Circuit.SetActiveBus(bus_name)
        voltages = dss.Bus.puVmagAngle()
        voltage_pu = voltages[0] if voltages else 0.0

        return {
            "success": True,
            "pv_name": pv_name,
            "kw": round(kw, 4),
            "kvar": round(kvar, 4),
            "kva": round(kva, 4),
            "pf": round(pf, 4),
            "voltage_pu": round(voltage_pu, 4),
            "errors": []
        }

    except Exception as e:
        logger.error(f"Error getting inverter status for {pv_name}: {e}")
        return {
            "success": False,
            "pv_name": pv_name,
            "kw": 0.0,
            "kvar": 0.0,
            "kva": 0.0,
            "pf": 0.0,
            "voltage_pu": 0.0,
            "errors": [str(e)]
        }


def list_available_curves() -> list[dict[str, str]]:
    """List all available standard control curves.

    Returns:
        List of dictionaries containing curve information:
            - name: Curve name (for use with load_curve)
            - file: JSON filename
            - description: Curve description from JSON file
            - type: Control type (volt-var, volt-watt, etc.)

    Example:
        >>> curves = list_available_curves()
        >>> for curve in curves:
        ...     print(f"{curve['name']}: {curve['description']}")
        IEEE1547: IEEE 1547-2018 Category B volt-var curve
        RULE21: California Rule 21 volt-var curve
    """
    curves_info = []

    for name, filename in STANDARD_CURVES.items():
        try:
            curve_path = CURVES_DIR / filename
            with open(curve_path, "r") as f:
                data = json.load(f)

            curves_info.append({
                "name": name,
                "file": filename,
                "description": data.get("description", "No description"),
                "type": data.get("type", "unknown")
            })
        except Exception as e:
            logger.warning(f"Could not load curve info for {name}: {e}")

    return curves_info
