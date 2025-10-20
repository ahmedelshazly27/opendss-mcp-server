"""
Time-Series Simulation Tool for OpenDSS MCP Server.

This module provides functionality to run time-series power flow simulations
with load and generation profiles.
"""

import logging
from pathlib import Path
from typing import Any
import json
import opendssdirect as dss

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_time_series_simulation(
    load_profile: str | dict,
    generation_profile: str | dict | None = None,
    duration_hours: int = 24,
    timestep_minutes: int = 60,
    output_variables: list[str] | None = None,
) -> dict[str, Any]:
    """
    Run time-series power flow simulation with load and generation profiles.

    This function simulates the electrical system over a specified time period,
    scaling loads and generation according to provided profiles. It collects
    detailed time-series data and calculates summary statistics.

    Args:
        load_profile: Load profile to apply. Either:
            - String: Path or name of JSON profile file (e.g., "residential_summer")
            - Dict: Profile data with "multipliers" key
        generation_profile: Optional generation profile. Either:
            - String: Path or name of JSON profile file (e.g., "solar_clear_day")
            - Dict: Profile data with "multipliers" key
            - None: No generation scaling applied
        duration_hours: Simulation duration in hours (default: 24)
        timestep_minutes: Time step resolution in minutes (default: 60)
        output_variables: List of variables to track. Options:
            - "voltages": Per-bus voltage magnitudes (pu)
            - "losses": System losses (kW)
            - "loadings": Line loading percentages
            - "powers": Bus powers (kW, kvar)
            - Default: ["voltages", "losses", "loadings"]

    Returns:
        dict: Results dictionary with structure:
            {
                "success": bool,
                "data": {
                    "timesteps": list[dict],  # Per-timestep results
                    "summary": {
                        "duration_hours": float,
                        "num_timesteps": int,
                        "avg_losses_kw": float,
                        "peak_losses_kw": float,
                        "peak_load_kw": float,
                        "energy_served_kwh": float,
                        "min_voltage_pu": float,
                        "max_voltage_pu": float,
                        "avg_voltage_pu": float,
                        "max_line_loading_pct": float
                    },
                    "profiles_applied": {
                        "load_profile_name": str,
                        "generation_profile_name": str | None
                    }
                },
                "metadata": {...},
                "errors": list[str]
            }

    Example:
        >>> # Run 24-hour simulation with residential summer load
        >>> result = run_time_series_simulation(
        ...     load_profile="residential_summer",
        ...     generation_profile="solar_clear_day",
        ...     duration_hours=24,
        ...     timestep_minutes=60
        ... )
        >>> summary = result['data']['summary']
        >>> print(f"Average losses: {summary['avg_losses_kw']:.2f} kW")
        >>> print(f"Peak load: {summary['peak_load_kw']:.2f} kW")

        >>> # Run with custom profile dictionary
        >>> custom_profile = {
        ...     "name": "CUSTOM",
        ...     "multipliers": [0.5] * 24  # Constant 50% load
        ... }
        >>> result = run_time_series_simulation(
        ...     load_profile=custom_profile,
        ...     duration_hours=24
        ... )

        >>> # Access time-series data
        >>> timesteps = result['data']['timesteps']
        >>> for ts in timesteps[:3]:
        ...     print(f"Hour {ts['hour']}: {ts['total_load_kw']:.1f} kW")
    """
    errors: list[str] = []

    try:
        logger.info(
            f"Starting time-series simulation: duration={duration_hours}h, "
            f"timestep={timestep_minutes}min"
        )

        # Set default output variables
        if output_variables is None:
            output_variables = ["voltages", "losses", "loadings"]

        # Validate circuit is loaded
        if not _validate_circuit():
            return {
                "success": False,
                "data": {},
                "metadata": {},
                "errors": [
                    "No circuit loaded. Load a feeder first using load_ieee_test_feeder()."
                ],
            }

        # Load profile data
        load_profile_data, load_error = _load_profile_data(load_profile, "load")
        if load_error:
            errors.append(load_error)
            return {"success": False, "data": {}, "metadata": {}, "errors": errors}

        gen_profile_data = None
        if generation_profile is not None:
            gen_profile_data, gen_error = _load_profile_data(
                generation_profile, "generation"
            )
            if gen_error:
                errors.append(gen_error)
                return {"success": False, "data": {}, "metadata": {}, "errors": errors}

        # Get base load and generation values
        base_loads, total_base_load_kw = _get_base_loads()
        base_pvs = {}
        if gen_profile_data:
            base_pvs, _ = _get_base_pvs()

        # Calculate number of timesteps
        num_timesteps = int((duration_hours * 60) / timestep_minutes)

        # Validate profile lengths
        load_multipliers = load_profile_data["multipliers"]
        if len(load_multipliers) < num_timesteps:
            # Repeat profile if simulation is longer than profile
            repeats = (num_timesteps // len(load_multipliers)) + 1
            load_multipliers = (load_multipliers * repeats)[:num_timesteps]

        gen_multipliers = None
        if gen_profile_data:
            gen_multipliers = gen_profile_data["multipliers"]
            if len(gen_multipliers) < num_timesteps:
                repeats = (num_timesteps // len(gen_multipliers)) + 1
                gen_multipliers = (gen_multipliers * repeats)[:num_timesteps]

        # Run time-series simulation
        timesteps_data = []
        all_voltages = []
        all_losses = []
        all_loadings = []
        all_total_loads = []

        logger.info(f"Running {num_timesteps} timesteps...")

        for step in range(num_timesteps):
            # Calculate current hour
            hour = (step * timestep_minutes) / 60.0

            # Get multipliers for this timestep
            load_mult = load_multipliers[step]
            gen_mult = gen_multipliers[step] if gen_multipliers else 0.0

            # Scale loads
            for load_name, base_kw in base_loads.items():
                scaled_kw = base_kw * load_mult
                dss.Loads.Name(load_name)
                dss.Loads.kW(scaled_kw)

            # Scale generation
            if base_pvs:
                for pv_name, base_pmpp in base_pvs.items():
                    scaled_pmpp = base_pmpp * gen_mult
                    # Set via text command since PVSystems don't have direct kW setter
                    dss.Text.Command(f"PVSystem.{pv_name}.Pmpp={scaled_pmpp}")
                    dss.Text.Command(f"PVSystem.{pv_name}.irradiance={gen_mult}")

            # Solve power flow
            dss.Solution.Solve()
            converged = dss.Solution.Converged()

            if not converged:
                logger.warning(
                    f"Power flow did not converge at timestep {step} (hour {hour:.2f})"
                )

            # Collect results for this timestep
            timestep_result = {
                "timestep": step,
                "hour": round(hour, 4),
                "load_multiplier": round(load_mult, 4),
                "generation_multiplier": round(gen_mult, 4) if gen_multipliers else 0.0,
                "converged": converged,
            }

            # Calculate total load
            total_load_kw = total_base_load_kw * load_mult
            timestep_result["total_load_kw"] = round(total_load_kw, 2)
            all_total_loads.append(total_load_kw)

            # Collect requested output variables
            if "losses" in output_variables:
                losses = dss.Circuit.Losses()
                losses_kw = losses[0] / 1000.0
                timestep_result["losses_kw"] = round(losses_kw, 2)
                all_losses.append(losses_kw)

            if "voltages" in output_variables:
                voltages_pu = _get_all_bus_voltages()
                timestep_result["min_voltage_pu"] = round(min(voltages_pu.values()), 4)
                timestep_result["max_voltage_pu"] = round(max(voltages_pu.values()), 4)
                timestep_result["avg_voltage_pu"] = round(
                    sum(voltages_pu.values()) / len(voltages_pu), 4
                )
                all_voltages.extend(voltages_pu.values())

            if "loadings" in output_variables:
                line_loadings = _get_line_loadings()
                if line_loadings:
                    max_loading = max(line_loadings.values())
                    timestep_result["max_line_loading_pct"] = round(max_loading, 2)
                    all_loadings.append(max_loading)
                else:
                    timestep_result["max_line_loading_pct"] = 0.0

            if "powers" in output_variables:
                bus_powers = _get_bus_powers()
                timestep_result["bus_powers"] = bus_powers

            timesteps_data.append(timestep_result)

        logger.info("Time-series simulation completed successfully")

        # Calculate summary statistics
        summary = _calculate_summary_statistics(
            timesteps_data=timesteps_data,
            all_voltages=all_voltages,
            all_losses=all_losses,
            all_loadings=all_loadings,
            all_total_loads=all_total_loads,
            duration_hours=duration_hours,
            num_timesteps=num_timesteps,
            timestep_minutes=timestep_minutes,
        )

        # Prepare result
        result = {
            "success": True,
            "data": {
                "timesteps": timesteps_data,
                "summary": summary,
                "profiles_applied": {
                    "load_profile_name": load_profile_data.get("name", "CUSTOM"),
                    "generation_profile_name": (
                        gen_profile_data.get("name", "CUSTOM")
                        if gen_profile_data
                        else None
                    ),
                },
            },
            "metadata": {
                "tool": "run_time_series_simulation",
                "duration_hours": duration_hours,
                "timestep_minutes": timestep_minutes,
                "num_timesteps": num_timesteps,
                "output_variables": output_variables,
            },
            "errors": errors,
        }

        return result

    except Exception as e:
        logger.error(f"Error in time-series simulation: {e}", exc_info=True)
        errors.append(f"Simulation error: {str(e)}")
        return {"success": False, "data": {}, "metadata": {}, "errors": errors}


def _validate_circuit() -> bool:
    """Validate that a circuit is loaded in OpenDSS."""
    try:
        circuit_name = dss.Circuit.Name()
        return circuit_name != "" and circuit_name is not None
    except Exception:
        return False


def _load_profile_data(
    profile: str | dict, profile_type: str
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Load profile data from file or dictionary.

    Args:
        profile: Profile name, path, or dictionary
        profile_type: "load" or "generation" (for error messages)

    Returns:
        Tuple of (profile_data, error_message)
    """
    try:
        # If dict, return as-is
        if isinstance(profile, dict):
            if "multipliers" not in profile:
                return None, f"{profile_type} profile dict must have 'multipliers' key"
            return profile, None

        # If string, load from file
        profile_str = str(profile)

        # Try as profile name (without .json extension)
        profiles_dir = Path(__file__).parent.parent / "data" / "load_profiles"

        # Try exact path first
        profile_path = Path(profile_str)
        if not profile_path.exists():
            # Try in load_profiles directory
            profile_path = profiles_dir / f"{profile_str}.json"

        if not profile_path.exists():
            # Try without adding .json (maybe user provided full filename)
            profile_path = profiles_dir / profile_str

        if not profile_path.exists():
            return None, f"{profile_type} profile not found: {profile_str}"

        # Load JSON file
        with open(profile_path, "r") as f:
            data = json.load(f)

        if "multipliers" not in data:
            return (
                None,
                f"{profile_type} profile missing 'multipliers' field: {profile_path}",
            )

        return data, None

    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {profile_type} profile: {e}"
    except Exception as e:
        return None, f"Error loading {profile_type} profile: {e}"


def _get_base_loads() -> tuple[dict[str, float], float]:
    """
    Get base load values for all loads in the circuit.

    Returns:
        Tuple of (dict mapping load_name to base_kw, total_base_load_kw)
    """
    base_loads = {}
    total_base_kw = 0.0

    load_names = dss.Loads.AllNames()
    if not load_names:
        return base_loads, total_base_kw

    for load_name in load_names:
        dss.Loads.Name(load_name)
        base_kw = dss.Loads.kW()
        base_loads[load_name] = base_kw
        total_base_kw += base_kw

    return base_loads, total_base_kw


def _get_base_pvs() -> tuple[dict[str, float], float]:
    """
    Get base generation values for all PV systems in the circuit.

    Returns:
        Tuple of (dict mapping pv_name to base_pmpp, total_base_pmpp)
    """
    base_pvs = {}
    total_base_pmpp = 0.0

    # Get all PVSystem elements
    pv_names = dss.PVsystems.AllNames()
    if not pv_names:
        return base_pvs, total_base_pmpp

    for pv_name in pv_names:
        dss.PVsystems.Name(pv_name)
        base_pmpp = dss.PVsystems.Pmpp()
        base_pvs[pv_name] = base_pmpp
        total_base_pmpp += base_pmpp

    return base_pvs, total_base_pmpp


def _get_all_bus_voltages() -> dict[str, float]:
    """
    Get voltage magnitudes (pu) for all buses.

    Returns:
        Dict mapping bus_name to voltage_pu
    """
    voltages = {}

    all_bus_names = dss.Circuit.AllBusNames()
    if not all_bus_names:
        return voltages

    for bus_name in all_bus_names:
        dss.Circuit.SetActiveBus(bus_name)
        bus_voltages = dss.Bus.puVmagAngle()

        # Get magnitude values (even indices)
        mags = [bus_voltages[i] for i in range(0, len(bus_voltages), 2)]

        # Use average voltage if multi-phase
        if mags:
            avg_voltage = sum(mags) / len(mags)
            voltages[bus_name] = avg_voltage

    return voltages


def _get_line_loadings() -> dict[str, float]:
    """
    Get loading percentages for all lines.

    Returns:
        Dict mapping line_name to loading_percent
    """
    loadings = {}

    line_names = dss.Lines.AllNames()
    if not line_names:
        return loadings

    for line_name in line_names:
        dss.Lines.Name(line_name)
        # Get normal amps rating
        norm_amps = dss.Lines.NormAmps()

        if norm_amps > 0:
            # Set active element and get currents
            dss.Circuit.SetActiveElement(f"Line.{line_name}")
            currents = dss.CktElement.CurrentsMagAng()

            # Get magnitude values (even indices)
            current_mags = [currents[i] for i in range(0, len(currents), 2)]

            if current_mags:
                max_current = max(current_mags)
                loading_pct = (max_current / norm_amps) * 100.0
                loadings[line_name] = loading_pct

    return loadings


def _get_bus_powers() -> dict[str, dict[str, float]]:
    """
    Get power values (kW, kvar) for all buses.

    Returns:
        Dict mapping bus_name to {"kw": float, "kvar": float}
    """
    bus_powers = {}

    # Get powers by summing all loads and generators at each bus
    all_bus_names = dss.Circuit.AllBusNames()
    if not all_bus_names:
        return bus_powers

    # Initialize power dict for all buses
    for bus_name in all_bus_names:
        bus_powers[bus_name] = {"kw": 0.0, "kvar": 0.0}

    # Sum load powers
    load_names = dss.Loads.AllNames()
    if load_names:
        for load_name in load_names:
            dss.Loads.Name(load_name)
            # Get bus connection
            dss.Circuit.SetActiveElement(f"Load.{load_name}")
            bus_name = dss.CktElement.BusNames()[0].split(".")[0]

            # Get powers
            powers = dss.CktElement.Powers()
            # Sum kW and kvar (powers array is [kW1, kvar1, kW2, kvar2, ...])
            load_kw = sum(powers[i] for i in range(0, len(powers), 2))
            load_kvar = sum(powers[i] for i in range(1, len(powers), 2))

            if bus_name in bus_powers:
                bus_powers[bus_name]["kw"] += load_kw
                bus_powers[bus_name]["kvar"] += load_kvar

    # Sum PV powers (if any)
    pv_names = dss.PVsystems.AllNames()
    if pv_names:
        for pv_name in pv_names:
            dss.PVsystems.Name(pv_name)
            # Get bus connection
            dss.Circuit.SetActiveElement(f"PVSystem.{pv_name}")
            bus_name = dss.CktElement.BusNames()[0].split(".")[0]

            # Get powers
            powers = dss.CktElement.Powers()
            pv_kw = sum(powers[i] for i in range(0, len(powers), 2))
            pv_kvar = sum(powers[i] for i in range(1, len(powers), 2))

            if bus_name in bus_powers:
                bus_powers[bus_name]["kw"] += pv_kw
                bus_powers[bus_name]["kvar"] += pv_kvar

    # Round values
    for bus_name in bus_powers:
        bus_powers[bus_name]["kw"] = round(bus_powers[bus_name]["kw"], 2)
        bus_powers[bus_name]["kvar"] = round(bus_powers[bus_name]["kvar"], 2)

    return bus_powers


def _calculate_summary_statistics(
    timesteps_data: list[dict],
    all_voltages: list[float],
    all_losses: list[float],
    all_loadings: list[float],
    all_total_loads: list[float],
    duration_hours: int,
    num_timesteps: int,
    timestep_minutes: int,
) -> dict[str, Any]:
    """
    Calculate summary statistics from time-series data.

    Returns:
        Dict with summary statistics
    """
    summary = {
        "duration_hours": duration_hours,
        "num_timesteps": num_timesteps,
        "timestep_minutes": timestep_minutes,
    }

    # Losses statistics
    if all_losses:
        summary["avg_losses_kw"] = round(sum(all_losses) / len(all_losses), 2)
        summary["peak_losses_kw"] = round(max(all_losses), 2)
        summary["min_losses_kw"] = round(min(all_losses), 2)

    # Load statistics
    if all_total_loads:
        summary["peak_load_kw"] = round(max(all_total_loads), 2)
        summary["min_load_kw"] = round(min(all_total_loads), 2)
        summary["avg_load_kw"] = round(sum(all_total_loads) / len(all_total_loads), 2)

        # Calculate energy served (kWh)
        # Energy = average power * time
        timestep_hours = timestep_minutes / 60.0
        energy_kwh = sum(load_kw * timestep_hours for load_kw in all_total_loads)
        summary["energy_served_kwh"] = round(energy_kwh, 2)

    # Voltage statistics
    if all_voltages:
        summary["min_voltage_pu"] = round(min(all_voltages), 4)
        summary["max_voltage_pu"] = round(max(all_voltages), 4)
        summary["avg_voltage_pu"] = round(sum(all_voltages) / len(all_voltages), 4)

    # Loading statistics
    if all_loadings:
        summary["max_line_loading_pct"] = round(max(all_loadings), 2)
        summary["avg_line_loading_pct"] = round(
            sum(all_loadings) / len(all_loadings), 2
        )

    # Convergence statistics
    converged_count = sum(1 for ts in timesteps_data if ts.get("converged", False))
    summary["convergence_rate_pct"] = round((converged_count / num_timesteps) * 100, 2)

    return summary
