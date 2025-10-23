"""
OpenDSS Model Context Protocol (MCP) Server.

This module implements an MCP server for OpenDSS power system simulations,
providing comprehensive tools for distribution planning, DER integration analysis,
and power quality assessment. Reduces distribution planning studies from weeks to minutes
through conversational AI interaction.
"""

import logging
import sys
from typing import Any, Dict, Optional

# MCP SDK imports
from mcp.server.fastmcp import FastMCP

# Local imports - All 7 tools
from .tools.feeder_loader import load_ieee_test_feeder
from .tools.power_flow import run_power_flow
from .tools.voltage_checker import check_voltage_violations
from .tools.capacity import analyze_feeder_capacity
from .tools.der_optimizer import optimize_der_placement
from .tools.timeseries import run_time_series_simulation
from .tools.visualization import generate_visualization

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP(name="opendss-mcp-server")


@mcp.tool()
def load_feeder(
    feeder_id: str, modifications: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Load an IEEE test feeder into the OpenDSS engine.

    Args:
        feeder_id: Identifier of the IEEE test feeder (e.g., 'IEEE13', 'IEEE34', 'IEEE123')
        modifications: Optional dictionary of modifications to apply to the feeder

    Returns:
        Dictionary containing the loaded feeder data and metadata
    """
    try:
        logger.info(f"Loading feeder: {feeder_id}")
        result = load_ieee_test_feeder(feeder_id, modifications or {})

        if not result.get("success", False):
            error_msg = result.get("errors", ["Unknown error loading feeder"])
            logger.error(f"Failed to load feeder {feeder_id}: {error_msg}")

        return result

    except Exception as e:
        error_msg = f"Error loading feeder {feeder_id}: {str(e)}"
        logger.exception(error_msg)
        return {"success": False, "data": None, "metadata": None, "errors": [error_msg]}


@mcp.tool()
def run_power_flow_analysis(
    feeder_id: str, options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run power flow analysis on a loaded feeder.

    Args:
        feeder_id: Identifier of the IEEE test feeder
        options: Dictionary of power flow options
            - max_iterations: Maximum number of iterations (default: 100)
            - tolerance: Convergence tolerance (default: 0.0001)
            - control_mode: Control mode for the solution (default: 'snapshot')

    Returns:
        Dictionary containing power flow results and metadata
    """
    try:
        logger.info(f"Running power flow for feeder: {feeder_id}")
        result = run_power_flow(feeder_id, options or {})

        if not result.get("success", False):
            error_msg = result.get("errors", ["Unknown error running power flow"])
            logger.error(f"Power flow failed for {feeder_id}: {error_msg}")

        return result

    except Exception as e:
        error_msg = f"Error running power flow for {feeder_id}: {str(e)}"
        logger.exception(error_msg)
        return {"success": False, "data": None, "metadata": None, "errors": [error_msg]}


@mcp.tool()
def check_voltages(
    min_voltage_pu: float = 0.95,
    max_voltage_pu: float = 1.05,
    phase: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Check all bus voltages against specified limits and identify violations.

    Args:
        min_voltage_pu: Minimum acceptable voltage in per-unit (default: 0.95)
        max_voltage_pu: Maximum acceptable voltage in per-unit (default: 1.05)
        phase: Optional phase filter ('1', '2', '3', or None for all phases)

    Returns:
        Dictionary containing violations list, summary statistics, and metadata
    """
    try:
        logger.info(
            f"Checking voltage violations with limits [{min_voltage_pu}, {max_voltage_pu}] pu"
        )
        result = check_voltage_violations(min_voltage_pu, max_voltage_pu, phase)

        if not result.get("success", False):
            error_msg = result.get("errors", ["Unknown error checking voltages"])
            logger.error(f"Voltage check failed: {error_msg}")
        else:
            num_violations = (
                result.get("data", {}).get("summary", {}).get("total_violations", 0)
            )
            logger.info(f"Found {num_violations} voltage violations")

        return result

    except Exception as e:
        error_msg = f"Error checking voltage violations: {str(e)}"
        logger.exception(error_msg)
        return {"success": False, "data": None, "metadata": None, "errors": [error_msg]}


@mcp.tool()
def analyze_capacity(
    bus_id: str,
    der_type: str = "solar",
    increment_kw: float = 100,
    max_capacity_kw: float = 10000,
    constraints: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Analyze maximum DER hosting capacity at a specific bus.

    Args:
        bus_id: Identifier of the bus where DER will be connected
        der_type: Type of DER ("solar", "battery", "wind") - default: "solar"
        increment_kw: Capacity increment for each iteration in kW (default: 100)
        max_capacity_kw: Maximum capacity to test in kW (default: 10000)
        constraints: Optional constraint limits (min_voltage_pu, max_voltage_pu, max_line_loading_pct)

    Returns:
        Dictionary containing capacity analysis results with max capacity, limiting constraint, and capacity curve
    """
    try:
        logger.info(f"Analyzing capacity at bus {bus_id} for {der_type} DER")
        result = analyze_feeder_capacity(
            bus_id, der_type, increment_kw, max_capacity_kw, constraints or {}
        )

        if not result.get("success", False):
            error_msg = result.get("errors", ["Unknown error analyzing capacity"])
            logger.error(f"Capacity analysis failed: {error_msg}")
        else:
            max_capacity = result.get("data", {}).get("max_capacity_kw", 0)
            limiting = result.get("data", {}).get("limiting_constraint", "none")
            logger.info(f"Max capacity: {max_capacity} kW, limited by: {limiting}")

        return result

    except Exception as e:
        error_msg = f"Error analyzing feeder capacity: {str(e)}"
        logger.exception(error_msg)
        return {"success": False, "data": None, "metadata": None, "errors": [error_msg]}


@mcp.tool()
def optimize_der(
    der_type: str,
    capacity_kw: float,
    battery_kwh: Optional[float] = None,
    objective: str = "minimize_losses",
    candidate_buses: Optional[list] = None,
    constraints: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Optimize DER placement to achieve specified objective.

    Args:
        der_type: Type of DER ("solar", "battery", "solar_battery", "ev_charger", "wind")
        capacity_kw: DER capacity in kW
        battery_kwh: Battery energy capacity in kWh (optional)
        objective: Optimization objective ("minimize_losses", "maximize_capacity", "minimize_violations")
        candidate_buses: List of bus IDs to evaluate (None = all buses, limited to 20)
        constraints: Optional constraint limits (min_voltage_pu, max_voltage_pu, max_candidates)

    Returns:
        Dictionary containing optimal bus, improvement metrics, and comparison table
    """
    try:
        logger.info(
            f"Optimizing {der_type} DER placement ({capacity_kw} kW) with objective: {objective}"
        )
        result = optimize_der_placement(
            der_type,
            capacity_kw,
            battery_kwh,
            objective,
            candidate_buses,
            constraints or {},
        )

        if not result.get("success", False):
            error_msg = result.get("errors", ["Unknown error optimizing DER placement"])
            logger.error(f"DER optimization failed: {error_msg}")
        else:
            optimal_bus = result.get("data", {}).get("optimal_bus", "unknown")
            improvement = result.get("data", {}).get("improvement_metrics", {})
            logger.info(
                f"Optimal bus: {optimal_bus}, Loss reduction: {improvement.get('loss_reduction_kw', 0)} kW"
            )

        return result

    except Exception as e:
        error_msg = f"Error optimizing DER placement: {str(e)}"
        logger.exception(error_msg)
        return {"success": False, "data": None, "metadata": None, "errors": [error_msg]}


@mcp.tool()
def run_timeseries(
    load_profile: str | dict,
    generation_profile: Optional[str | dict] = None,
    duration_hours: int = 24,
    timestep_minutes: int = 60,
    output_variables: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Run time-series power flow simulation with load and generation profiles.

    Simulates the electrical system over time with varying loads and generation.
    Useful for analyzing daily operations, renewable integration, and energy management.

    Args:
        load_profile: Load profile to apply. Either:
            - String: Name of profile file (e.g., "residential_summer")
            - Dict: Custom profile with "multipliers" key (list of scaling factors)
        generation_profile: Optional generation profile (PV, wind, etc.):
            - String: Name of profile file (e.g., "solar_clear_day")
            - Dict: Custom profile with "multipliers" key
            - None: No generation scaling
        duration_hours: Simulation duration in hours (default: 24 for daily analysis)
        timestep_minutes: Time step resolution in minutes (default: 60 for hourly)
        output_variables: Variables to track (default: ["voltages", "losses", "loadings"]):
            - "voltages": Bus voltages per timestep
            - "losses": System losses per timestep
            - "loadings": Line loading percentages
            - "powers": Bus power injections

    Returns:
        Dictionary with time-series results, summary statistics, and convergence info
    """
    try:
        logger.info(
            f"Running time-series simulation: {duration_hours}h at {timestep_minutes}min steps"
        )
        result = run_time_series_simulation(
            load_profile=load_profile,
            generation_profile=generation_profile,
            duration_hours=duration_hours,
            timestep_minutes=timestep_minutes,
            output_variables=output_variables,
        )

        if not result.get("success", False):
            error_msg = result.get(
                "errors", ["Unknown error in time-series simulation"]
            )
            logger.error(f"Time-series simulation failed: {error_msg}")
        else:
            num_steps = (
                result.get("data", {}).get("summary", {}).get("num_timesteps", 0)
            )
            convergence_rate = (
                result.get("data", {}).get("summary", {}).get("convergence_rate_pct", 0)
            )
            logger.info(
                f"Time-series complete: {num_steps} timesteps, {convergence_rate}% convergence"
            )

        return result

    except Exception as e:
        error_msg = f"Error in time-series simulation: {str(e)}"
        logger.exception(error_msg)
        return {"success": False, "data": None, "metadata": None, "errors": [error_msg]}


@mcp.tool()
def create_visualization(
    plot_type: str,
    data_source: str = "last_power_flow",
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate professional visualizations for power system analysis results.

    Creates publication-quality plots for reports and presentations. Supports both
    file export and base64 encoding for web applications.

    Args:
        plot_type: Type of visualization to generate:
            - "voltage_profile": Bar chart showing bus voltages with violation highlighting
            - "network_diagram": Network topology diagram with voltage-colored nodes
            - "timeseries": Multi-panel line plots for time-varying data
            - "capacity_curve": Scatter plot for DER hosting capacity analysis
            - "harmonics_spectrum": Bar chart of harmonic voltage magnitudes
        data_source: Source of data to visualize (default: "last_power_flow"):
            - "circuit": Query current OpenDSS circuit state
            - "last_power_flow": Use most recent power flow results
            - "last_timeseries": Use most recent time-series simulation
            - "last_capacity": Use most recent capacity analysis
            - "last_harmonics": Use most recent harmonics analysis
        options: Plot customization options:
            - save_path: Path to save file (if None, returns base64-encoded PNG)
            - figsize: (width, height) in inches (e.g., (12, 6))
            - dpi: Resolution in dots per inch (default: 100, use 300 for publication)
            - title: Custom plot title
            - show_violations: Highlight voltage violations with colors (default: True)
            - bus_filter: List of specific buses to include (None = all)

    Returns:
        Dictionary with visualization data (file path or base64 image) and metadata
    """
    try:
        logger.info(f"Creating {plot_type} visualization from {data_source}")
        result = generate_visualization(plot_type, data_source, options or {})

        if not result.get("success", False):
            error_msg = result.get("errors", ["Unknown error creating visualization"])
            logger.error(f"Visualization failed: {error_msg}")
        else:
            if result.get("data", {}).get("file_path"):
                logger.info(f"Visualization saved to: {result['data']['file_path']}")
            else:
                logger.info("Visualization created as base64 image")

        return result

    except Exception as e:
        error_msg = f"Error creating visualization: {str(e)}"
        logger.exception(error_msg)
        return {"success": False, "data": None, "metadata": None, "errors": [error_msg]}


def main() -> None:
    """Start the MCP server with stdio transport."""
    try:
        logger.info("Starting OpenDSS MCP Server")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.critical(f"Server error: {str(e)}", exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
