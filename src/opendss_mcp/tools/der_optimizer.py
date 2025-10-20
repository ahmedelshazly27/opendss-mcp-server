"""
DER placement optimization module for OpenDSS.

This module provides functions for optimizing the placement of Distributed Energy
Resources (DER) based on specified objectives such as minimizing losses or
maximizing capacity utilization.
"""

import logging
from typing import Any, Dict, List, Optional

import opendssdirect as dss

from ..utils.formatters import format_success_response, format_error_response
from ..utils.validators import validate_positive_float
from ..utils.inverter_control import load_curve, configure_volt_var_control
from .voltage_checker import check_voltage_violations

logger = logging.getLogger(__name__)

# Supported DER types
SUPPORTED_DER_TYPES = [
    "solar",
    "battery",
    "solar_battery",
    "ev_charger",
    "wind",
    "solar_vvc",
    "solar_battery_vvc",  # Volt-var control enabled variants
]

# Supported optimization objectives
SUPPORTED_OBJECTIVES = ["minimize_losses", "maximize_capacity", "minimize_violations"]


def _get_total_losses() -> float:
    """Get total system losses in kW.

    Returns:
        Total losses in kW
    """
    try:
        losses_kw, _ = dss.Circuit.Losses()
        return losses_kw / 1000.0  # Convert from W to kW
    except Exception as e:
        logger.error(f"Error getting losses: {e}")
        return 0.0


def _get_der_reactive_power(bus_id: str, der_type: str) -> float:
    """Get reactive power output from DER at specified bus.

    Args:
        bus_id: Bus identifier
        der_type: Type of DER

    Returns:
        Reactive power in kvar (positive = absorbing, negative = injecting)
    """
    try:
        der_name = f"der_opt_{bus_id}"
        base_type = der_type.replace("_vvc", "")

        # Determine element name based on type
        if base_type in ["solar", "wind"]:
            if base_type == "solar":
                element_name = f"PVSystem.{der_name}"
            else:
                element_name = f"Generator.{der_name}"

            # Set active element
            result = dss.Circuit.SetActiveElement(element_name)
            if result < 0:
                return 0.0

            # Get powers: [P1, Q1, P2, Q2, ...] for each terminal
            powers = dss.CktElement.Powers()
            if len(powers) >= 2:
                # Sum reactive power across all phases (odd indices)
                q_kvar = sum(powers[i] for i in range(1, len(powers), 2))
                return q_kvar
            return 0.0

        elif base_type == "solar_battery":
            # Get reactive power from PV component only
            element_name = f"PVSystem.{der_name}_pv"
            result = dss.Circuit.SetActiveElement(element_name)
            if result < 0:
                return 0.0

            powers = dss.CktElement.Powers()
            if len(powers) >= 2:
                q_kvar = sum(powers[i] for i in range(1, len(powers), 2))
                return q_kvar
            return 0.0

        else:
            # Battery, EV charger don't typically provide reactive power in this model
            return 0.0

    except Exception as e:
        logger.error(f"Error getting reactive power for {bus_id}: {e}")
        return 0.0


def _add_der_at_bus(
    bus_id: str,
    der_type: str,
    capacity_kw: float,
    battery_kwh: Optional[float] = None,
    control_settings: Optional[Dict[str, Any]] = None,
) -> bool:
    """Add a DER to the specified bus with optional volt-var control.

    Args:
        bus_id: Bus identifier
        der_type: Type of DER (supports "_vvc" suffix for volt-var control)
        capacity_kw: DER capacity in kW
        battery_kwh: Battery energy capacity in kWh (for battery types)
        control_settings: Optional control settings:
            - curve: Curve name ("IEEE1547", "RULE21") or path to JSON file
            - response_time: Response time in seconds (default: 10.0)

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

        # Parse DER type and check for volt-var control
        base_type = der_type.replace("_vvc", "")
        has_vvc = "_vvc" in der_type

        # Create unique DER name
        der_name = f"der_opt_{bus_id}"

        # Add DER based on base type
        if base_type == "solar":
            # Add PV system
            dss.Text.Command(
                f"New PVSystem.{der_name} Bus1={bus_id} kV={kv_base} kVA={capacity_kw} Pmpp={capacity_kw} irradiance=1.0"
            )

        elif base_type == "battery":
            # Add battery storage
            kwh = (
                battery_kwh if battery_kwh else capacity_kw * 4
            )  # Default 4-hour storage
            dss.Text.Command(
                f"New Storage.{der_name} Bus1={bus_id} kV={kv_base} kWrated={capacity_kw} kWhrated={kwh} %stored=50 %discharge=50"
            )

        elif base_type == "solar_battery":
            # Add both PV and storage
            dss.Text.Command(
                f"New PVSystem.{der_name}_pv Bus1={bus_id} kV={kv_base} kVA={capacity_kw} Pmpp={capacity_kw} irradiance=1.0"
            )
            kwh = (
                battery_kwh if battery_kwh else capacity_kw * 2
            )  # Default 2-hour for hybrid
            dss.Text.Command(
                f"New Storage.{der_name}_batt Bus1={bus_id} kV={kv_base} kWrated={capacity_kw * 0.5} kWhrated={kwh} %stored=50"
            )

        elif base_type == "ev_charger":
            # Add EV charger as load (negative for generation during V2G)
            dss.Text.Command(
                f"New Load.{der_name} Bus1={bus_id} kV={kv_base} kW={capacity_kw} PF=0.95"
            )

        elif base_type == "wind":
            # Add wind generator
            dss.Text.Command(
                f"New Generator.{der_name} Bus1={bus_id} kV={kv_base} kW={capacity_kw} PF=0.95"
            )

        else:
            logger.error(f"Unsupported DER type: {base_type}")
            return False

        # Configure volt-var control if requested
        if has_vvc and base_type in ["solar", "solar_battery"]:
            control_settings = control_settings or {}
            curve_name = control_settings.get("curve", "IEEE1547")
            response_time = control_settings.get("response_time", 10.0)

            try:
                # Load curve
                curve_points = load_curve(curve_name)

                # Configure volt-var for PV system(s)
                if base_type == "solar":
                    configure_volt_var_control(der_name, curve_points, response_time)
                elif base_type == "solar_battery":
                    configure_volt_var_control(
                        f"{der_name}_pv", curve_points, response_time
                    )

                logger.info(
                    f"Configured volt-var control for {der_name} with {curve_name} curve"
                )
            except Exception as e:
                logger.warning(f"Failed to configure volt-var control: {e}")
                # Continue without control - don't fail the entire operation

        return True

    except Exception as e:
        logger.error(f"Error adding DER: {e}")
        return False


def _remove_der_from_bus(bus_id: str, der_type: str) -> None:
    """Remove test DER from the circuit.

    Args:
        bus_id: Bus identifier
        der_type: Type of DER
    """
    try:
        der_name = f"der_opt_{bus_id}"

        # Try to disable all possible elements
        element_types = ["PVSystem", "Storage", "Generator", "Load"]

        for element_type in element_types:
            try:
                dss.Text.Command(f"{element_type}.{der_name}.enabled=no")
            except:
                pass

        # For solar_battery, also remove the separate components
        if der_type == "solar_battery":
            try:
                dss.Text.Command(f"PVSystem.{der_name}_pv.enabled=no")
                dss.Text.Command(f"Storage.{der_name}_batt.enabled=no")
            except:
                pass

    except Exception as e:
        logger.error(f"Error removing DER: {e}")


def _calculate_objective(
    objective: str,
    baseline_losses: float,
    current_losses: float,
    voltage_check: Dict[str, Any],
) -> float:
    """Calculate objective function value.

    Args:
        objective: Optimization objective
        baseline_losses: Baseline system losses in kW
        current_losses: Current system losses in kW
        voltage_check: Voltage violation check result

    Returns:
        Objective value (higher is better for ranking)
    """
    if objective == "minimize_losses":
        # Loss reduction in kW (positive is better)
        return baseline_losses - current_losses

    elif objective == "maximize_capacity":
        # Use loss reduction as proxy for capacity (more loss reduction = more capacity utilized)
        return baseline_losses - current_losses

    elif objective == "minimize_violations":
        # Negative count of violations (fewer violations is better)
        num_violations = (
            voltage_check.get("data", {}).get("summary", {}).get("total_violations", 0)
        )
        return -num_violations

    else:
        return 0.0


def optimize_der_placement(
    der_type: str,
    capacity_kw: float,
    battery_kwh: Optional[float] = None,
    objective: str = "minimize_losses",
    candidate_buses: Optional[List[str]] = None,
    constraints: Optional[Dict[str, Any]] = None,
    control_settings: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Optimize DER placement to achieve specified objective with optional volt-var control.

    This function evaluates multiple candidate bus locations for DER placement
    and identifies the optimal location based on the specified objective function.
    The analysis considers system losses, voltage profiles, constraint violations,
    and reactive power support (for volt-var enabled DERs).

    Args:
        der_type: Type of DER to place. Options:
            Without volt-var control:
                - "solar": Solar PV system
                - "battery": Battery storage
                - "solar_battery": Hybrid solar + battery
                - "ev_charger": EV charging station
                - "wind": Wind generator
            With volt-var control (append "_vvc"):
                - "solar_vvc": Solar PV with autonomous volt-var control
                - "solar_battery_vvc": Hybrid system with volt-var control

        capacity_kw: DER capacity in kW
        battery_kwh: Battery energy capacity in kWh (optional, defaults to 4x capacity_kw)
        objective: Optimization objective - "minimize_losses", "maximize_capacity",
                   or "minimize_violations" (default: "minimize_losses")
        candidate_buses: List of bus IDs to evaluate (None = evaluate all buses)
        constraints: Optional constraint limits:
            - min_voltage_pu: Minimum voltage limit (default: 0.95)
            - max_voltage_pu: Maximum voltage limit (default: 1.05)
            - max_candidates: Maximum number of candidates to evaluate (default: 20)
        control_settings: Optional volt-var control settings (for "_vvc" DER types):
            - curve: Control curve name ("IEEE1547", "RULE21") or path to custom JSON
            - response_time: Response time in seconds (default: 10.0)

    Returns:
        Dictionary containing:
            - success: Boolean indicating if the operation was successful
            - data: Dictionary with optimization results:
                - optimal_bus: Best bus location
                - optimal_capacity_kw: DER capacity
                - der_type: DER type used
                - objective: Optimization objective
                - improvement_metrics: Loss reduction, voltage improvements
                - comparison_table: Top candidates with metrics including q_support_kvar
                - baseline: Pre-DER system metrics
                - constraints: Voltage and loading constraints used
                - analysis_parameters: Number of candidates evaluated
            - metadata: Additional metadata about the optimization
            - errors: List of error messages if any occurred

    Example:
        >>> # Basic solar optimization (no volt-var control)
        >>> result = optimize_der_placement(
        ...     der_type="solar",
        ...     capacity_kw=500,
        ...     objective="minimize_losses"
        ... )
        >>> if result['success']:
        ...     optimal_bus = result['data']['optimal_bus']
        ...     improvement = result['data']['improvement_metrics']['loss_reduction_kw']
        ...     print(f"Best location: {optimal_bus}, Loss reduction: {improvement} kW")
        >>>
        >>> # Solar with IEEE 1547 volt-var control
        >>> result = optimize_der_placement(
        ...     der_type="solar_vvc",
        ...     capacity_kw=500,
        ...     objective="minimize_violations",
        ...     control_settings={
        ...         "curve": "IEEE1547",
        ...         "response_time": 10.0
        ...     }
        ... )
        >>> if result['success']:
        ...     comparison = result['data']['comparison_table']
        ...     for entry in comparison[:3]:
        ...         print(f"Bus {entry['bus_id']}: "
        ...               f"Loss reduction: {entry['loss_reduction_kw']} kW, "
        ...               f"Q support: {entry['q_support_kvar']} kvar")
        >>>
        >>> # Hybrid system with California Rule 21 control
        >>> result = optimize_der_placement(
        ...     der_type="solar_battery_vvc",
        ...     capacity_kw=500,
        ...     battery_kwh=2000,
        ...     control_settings={"curve": "RULE21"}
        ... )

    Note:
        - Volt-var control is only available for solar and solar_battery DER types
        - Control curves are loaded from src/opendss_mcp/data/control_curves/
        - Reactive power support (q_support_kvar) is included in results for VVC DERs
        - Positive q_support = absorbing vars (inductive), negative = injecting vars (capacitive)
    """
    try:
        # Validate inputs
        validate_positive_float(capacity_kw, "capacity_kw")

        if battery_kwh is not None:
            validate_positive_float(battery_kwh, "battery_kwh")

        if der_type not in SUPPORTED_DER_TYPES:
            return format_error_response(
                f"Unsupported DER type '{der_type}'. Supported types: {', '.join(SUPPORTED_DER_TYPES)}"
            )

        if objective not in SUPPORTED_OBJECTIVES:
            return format_error_response(
                f"Unsupported objective '{objective}'. Supported objectives: {', '.join(SUPPORTED_OBJECTIVES)}"
            )

        # Check if circuit is loaded
        if not dss.Circuit.Name():
            return format_error_response(
                "No circuit loaded. Please load a feeder first using load_feeder tool."
            )

        # Parse constraints
        constraints = constraints or {}
        min_voltage_pu = constraints.get("min_voltage_pu", 0.95)
        max_voltage_pu = constraints.get("max_voltage_pu", 1.05)
        max_candidates = constraints.get("max_candidates", 20)

        # Get baseline metrics
        dss.Solution.Solve()
        if not dss.Solution.Converged():
            return format_error_response("Baseline power flow did not converge")

        baseline_losses = _get_total_losses()
        baseline_voltage_check = check_voltage_violations(
            min_voltage_pu, max_voltage_pu
        )

        # Determine candidate buses
        if candidate_buses is None:
            # Use all buses, but limit to max_candidates
            all_buses = dss.Circuit.AllBusNames()
            candidate_buses = all_buses[:max_candidates]
            logger.info(f"Evaluating all buses (limited to {max_candidates})")
        else:
            # Validate provided buses exist
            all_buses_lower = [bus.lower() for bus in dss.Circuit.AllBusNames()]
            invalid_buses = [
                bus for bus in candidate_buses if bus.lower() not in all_buses_lower
            ]
            if invalid_buses:
                return format_error_response(
                    f"Invalid bus IDs: {', '.join(invalid_buses)}"
                )

        # Evaluate each candidate
        evaluation_results: List[Dict[str, Any]] = []

        for bus_id in candidate_buses:
            try:
                # Add DER at candidate bus
                if not _add_der_at_bus(
                    bus_id, der_type, capacity_kw, battery_kwh, control_settings
                ):
                    logger.warning(f"Failed to add DER at bus {bus_id}, skipping")
                    continue

                # Run power flow
                dss.Solution.Solve()

                if not dss.Solution.Converged():
                    logger.warning(
                        f"Power flow did not converge with DER at {bus_id}, skipping"
                    )
                    _remove_der_from_bus(bus_id, der_type)
                    continue

                # Get metrics
                current_losses = _get_total_losses()
                voltage_check = check_voltage_violations(min_voltage_pu, max_voltage_pu)
                num_violations = (
                    voltage_check.get("data", {})
                    .get("summary", {})
                    .get("total_violations", 0)
                )

                # Get reactive power support (for VVC-enabled DERs)
                q_support_kvar = (
                    _get_der_reactive_power(bus_id, der_type)
                    if "_vvc" in der_type
                    else 0.0
                )

                # Calculate objective value
                objective_value = _calculate_objective(
                    objective, baseline_losses, current_losses, voltage_check
                )

                # Store results
                evaluation_results.append(
                    {
                        "bus_id": bus_id,
                        "objective_value": round(objective_value, 4),
                        "losses_kw": round(current_losses, 2),
                        "loss_reduction_kw": round(baseline_losses - current_losses, 2),
                        "voltage_violations": num_violations,
                        "q_support_kvar": round(q_support_kvar, 2),
                        "converged": True,
                    }
                )

                # Remove DER for next iteration
                _remove_der_from_bus(bus_id, der_type)

            except Exception as e:
                logger.error(f"Error evaluating bus {bus_id}: {e}")
                _remove_der_from_bus(bus_id, der_type)
                continue

        # Check if we have any valid results
        if not evaluation_results:
            return format_error_response(
                "No valid candidate buses found. All candidates failed power flow convergence."
            )

        # Rank by objective value (higher is better)
        evaluation_results.sort(key=lambda x: x["objective_value"], reverse=True)

        # Get top candidate
        optimal_result = evaluation_results[0]
        optimal_bus = optimal_result["bus_id"]

        # Prepare comparison table (top 10)
        comparison_table = evaluation_results[:10]

        # Calculate improvement metrics
        improvement_metrics = {
            "loss_reduction_kw": optimal_result["loss_reduction_kw"],
            "loss_reduction_pct": (
                round((optimal_result["loss_reduction_kw"] / baseline_losses * 100), 2)
                if baseline_losses > 0
                else 0.0
            ),
            "voltage_violations_change": optimal_result["voltage_violations"]
            - baseline_voltage_check.get("data", {})
            .get("summary", {})
            .get("total_violations", 0),
        }

        # Prepare response data
        data = {
            "optimal_bus": optimal_bus,
            "optimal_capacity_kw": capacity_kw,
            "der_type": der_type,
            "objective": objective,
            "improvement_metrics": improvement_metrics,
            "comparison_table": comparison_table,
            "baseline": {
                "losses_kw": round(baseline_losses, 2),
                "voltage_violations": baseline_voltage_check.get("data", {})
                .get("summary", {})
                .get("total_violations", 0),
            },
            "constraints": {
                "min_voltage_pu": min_voltage_pu,
                "max_voltage_pu": max_voltage_pu,
            },
            "analysis_parameters": {
                "candidates_evaluated": len(evaluation_results),
                "candidates_requested": (
                    len(candidate_buses) if candidate_buses else "all"
                ),
            },
        }

        metadata = {
            "circuit_name": dss.Circuit.Name(),
            "analysis_type": "der_placement_optimization",
        }

        return format_success_response(data, metadata)

    except ValueError as e:
        return format_error_response(str(e))
    except Exception as e:
        error_msg = f"Error optimizing DER placement: {str(e)}"
        logger.exception(error_msg)
        return format_error_response(error_msg)
