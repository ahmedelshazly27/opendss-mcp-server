"""
Visualization Tool for OpenDSS MCP Server.

This module provides functionality to generate various plots and visualizations
for power system analysis results.
"""

import logging
from typing import Any
import base64
from io import BytesIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
import networkx as nx
import opendssdirect as dss

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Visualization state - stores data from last operations
_viz_state = {
    "last_power_flow": None,
    "last_timeseries": None,
    "last_capacity": None,
    "last_harmonics": None,
    "last_voltage_check": None,
}


def store_visualization_data(data_type: str, data: dict[str, Any]) -> None:
    """
    Store data for later visualization.

    Args:
        data_type: Type of data ("power_flow", "timeseries", "capacity", "harmonics", "voltage_check")
        data: Data dictionary to store
    """
    _viz_state[f"last_{data_type}"] = data


def generate_visualization(
    plot_type: str, data_source: str = "last_power_flow", options: dict | None = None
) -> dict[str, Any]:
    """
    Generate visualizations for power system analysis results.

    This function creates various types of plots including voltage profiles,
    network diagrams, time-series plots, and harmonic spectra. Plots can be
    saved to files or returned as base64-encoded images.

    Args:
        plot_type: Type of plot to generate. Options:
            - "voltage_profile": Bar chart of bus voltages across the system
            - "network_diagram": Network topology visualization with networkx
            - "timeseries": Line plots of variables over time
            - "capacity_curve": Scatter plot for capacity analysis
            - "harmonics_spectrum": Bar chart of harmonic magnitudes
        data_source: Source of data to plot. Options:
            - "last_power_flow": Use most recent power flow results
            - "last_timeseries": Use most recent time-series simulation
            - "last_capacity": Use most recent capacity analysis
            - "last_harmonics": Use most recent harmonics analysis
            - "last_voltage_check": Use most recent voltage check
            - "circuit": Query current OpenDSS circuit state
        options: Optional dictionary with plot customization:
            - save_path: Path to save plot file (if None, returns base64)
            - figsize: Tuple of (width, height) in inches (default: (10, 6))
            - dpi: Resolution in dots per inch (default: 100)
            - title: Custom plot title
            - xlabel: Custom x-axis label
            - ylabel: Custom y-axis label
            - color: Plot color (default varies by plot type)
            - show_grid: Whether to show grid (default: True)
            - show_violations: Highlight voltage violations (default: True)
            - variables: List of variables to plot for timeseries
            - bus_filter: List of buses to include (None = all)

    Returns:
        dict: Results dictionary with structure:
            {
                "success": bool,
                "data": {
                    "plot_type": str,
                    "file_path": str | None,  # If saved to file
                    "image_base64": str | None,  # If not saved
                    "format": str,  # "png", "pdf", etc.
                    "dimensions": {"width": int, "height": int}
                },
                "metadata": {...},
                "errors": list[str]
            }

    Example:
        >>> # Generate voltage profile from last power flow
        >>> result = generate_visualization(
        ...     plot_type="voltage_profile",
        ...     data_source="last_power_flow",
        ...     options={"save_path": "voltage_profile.png"}
        ... )
        >>> print(f"Saved to: {result['data']['file_path']}")

        >>> # Generate time-series plot with specific variables
        >>> result = generate_visualization(
        ...     plot_type="timeseries",
        ...     data_source="last_timeseries",
        ...     options={
        ...         "variables": ["losses_kw", "min_voltage_pu"],
        ...         "figsize": (12, 6)
        ...     }
        ... )
        >>> # Returns base64-encoded image if save_path not specified

        >>> # Generate network diagram
        >>> result = generate_visualization(
        ...     plot_type="network_diagram",
        ...     data_source="circuit",
        ...     options={"save_path": "network.png", "figsize": (14, 10)}
        ... )

        >>> # Generate harmonics spectrum
        >>> result = generate_visualization(
        ...     plot_type="harmonics_spectrum",
        ...     data_source="last_harmonics",
        ...     options={"bus_filter": ["650", "632", "671"]}
        ... )
    """
    errors: list[str] = []

    try:
        logger.info(f"Generating {plot_type} visualization from {data_source}")

        # Set default options
        if options is None:
            options = {}

        save_path = options.get("save_path")
        figsize = options.get("figsize", (10, 6))
        dpi = options.get("dpi", 100)

        # Retrieve data
        data = _get_data_for_visualization(data_source)
        if data is None:
            errors.append(f"No data available for source: {data_source}")
            return {"success": False, "data": {}, "metadata": {}, "errors": errors}

        # Generate the requested plot
        if plot_type == "voltage_profile":
            fig = _plot_voltage_profile(data, options)
        elif plot_type == "network_diagram":
            fig = _plot_network_diagram(data, options)
        elif plot_type == "timeseries":
            fig = _plot_timeseries(data, options)
        elif plot_type == "capacity_curve":
            fig = _plot_capacity_curve(data, options)
        elif plot_type == "harmonics_spectrum":
            fig = _plot_harmonics_spectrum(data, options)
        else:
            errors.append(f"Unknown plot type: {plot_type}")
            return {"success": False, "data": {}, "metadata": {}, "errors": errors}

        # Save or encode the plot
        image_base64 = None
        file_path = None

        if save_path:
            # Save to file
            save_path_obj = Path(save_path)
            fig.savefig(save_path_obj, dpi=dpi, bbox_inches="tight")
            file_path = str(save_path_obj.absolute())
            logger.info(f"Saved plot to: {file_path}")
        else:
            # Convert to base64
            buffer = BytesIO()
            fig.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight")
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
            buffer.close()

        plt.close(fig)

        # Get dimensions
        width_inches, height_inches = fig.get_size_inches()
        width_px = int(width_inches * dpi)
        height_px = int(height_inches * dpi)

        # Prepare result
        result = {
            "success": True,
            "data": {
                "plot_type": plot_type,
                "file_path": file_path,
                "image_base64": image_base64,
                "format": "png",
                "dimensions": {"width": width_px, "height": height_px},
            },
            "metadata": {
                "tool": "generate_visualization",
                "data_source": data_source,
                "figsize": figsize,
                "dpi": dpi,
            },
            "errors": errors,
        }

        return result

    except Exception as e:
        logger.error(f"Error generating visualization: {e}", exc_info=True)
        errors.append(f"Visualization error: {str(e)}")
        return {"success": False, "data": {}, "metadata": {}, "errors": errors}


def _get_data_for_visualization(data_source: str) -> dict[str, Any] | None:
    """
    Retrieve data for visualization based on source.

    Args:
        data_source: Data source identifier

    Returns:
        Data dictionary or None if not available
    """
    if data_source == "circuit":
        # Query current circuit state
        return _query_circuit_state()

    # Check stored state
    if data_source in _viz_state:
        return _viz_state[data_source]

    return None


def _query_circuit_state() -> dict[str, Any]:
    """
    Query current OpenDSS circuit state for visualization.

    Returns:
        Dictionary with circuit data
    """
    data = {"buses": [], "voltages": {}, "lines": []}

    # Get all buses and voltages
    all_bus_names = dss.Circuit.AllBusNames()
    for bus_name in all_bus_names:
        dss.Circuit.SetActiveBus(bus_name)
        bus_voltages = dss.Bus.puVmagAngle()
        mags = [bus_voltages[i] for i in range(0, len(bus_voltages), 2)]
        if mags:
            avg_voltage = sum(mags) / len(mags)
            data["buses"].append(bus_name)
            data["voltages"][bus_name] = avg_voltage

    # Get all lines
    line_names = dss.Lines.AllNames()
    if line_names:
        for line_name in line_names:
            dss.Lines.Name(line_name)
            bus1 = dss.Lines.Bus1().split(".")[0]
            bus2 = dss.Lines.Bus2().split(".")[0]
            data["lines"].append({"name": line_name, "bus1": bus1, "bus2": bus2})

    return data


def _plot_voltage_profile(data: dict[str, Any], options: dict) -> plt.Figure:
    """
    Create voltage profile bar chart.

    Args:
        data: Data dictionary with voltage information
        options: Plot options

    Returns:
        Matplotlib figure
    """
    # Extract voltage data
    if "voltages" in data:
        voltages = data["voltages"]
    elif "data" in data and "voltages" in data["data"]:
        voltages = data["data"]["voltages"]
    else:
        raise ValueError("No voltage data found in data source")

    # Apply bus filter if specified
    bus_filter = options.get("bus_filter")
    if bus_filter:
        voltages = {bus: v for bus, v in voltages.items() if bus in bus_filter}

    # Sort by bus name
    sorted_buses = sorted(voltages.keys())
    sorted_voltages = [voltages[bus] for bus in sorted_buses]

    # Create figure
    figsize = options.get("figsize", (12, 6))
    fig, ax = plt.subplots(figsize=figsize)

    # Determine colors (highlight violations if enabled)
    show_violations = options.get("show_violations", True)
    colors = []
    for v in sorted_voltages:
        if show_violations and (v < 0.95 or v > 1.05):
            colors.append("red")
        elif show_violations and (v < 0.97 or v > 1.03):
            colors.append("orange")
        else:
            colors.append(options.get("color", "steelblue"))

    # Create bar chart
    x_pos = range(len(sorted_buses))
    bars = ax.bar(
        x_pos, sorted_voltages, color=colors, edgecolor="black", linewidth=0.5
    )

    # Add ANSI limits
    ax.axhline(
        y=1.05, color="r", linestyle="--", linewidth=1.5, label="ANSI Upper (1.05 pu)"
    )
    ax.axhline(
        y=0.95, color="r", linestyle="--", linewidth=1.5, label="ANSI Lower (0.95 pu)"
    )
    ax.axhline(
        y=1.0,
        color="g",
        linestyle="-",
        linewidth=1,
        alpha=0.5,
        label="Nominal (1.0 pu)",
    )

    # Customize plot
    title = options.get("title", "Bus Voltage Profile")
    xlabel = options.get("xlabel", "Bus")
    ylabel = options.get("ylabel", "Voltage (pu)")

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(sorted_buses, rotation=45, ha="right")
    ax.legend(loc="best")

    if options.get("show_grid", True):
        ax.grid(True, alpha=0.3, linestyle="--")

    ax.set_ylim([0.9, 1.1])

    plt.tight_layout()
    return fig


def _plot_network_diagram(data: dict[str, Any], options: dict) -> plt.Figure:
    """
    Create network topology diagram using networkx.

    Args:
        data: Data dictionary with network topology
        options: Plot options

    Returns:
        Matplotlib figure
    """
    # Extract network data
    if "lines" in data:
        lines = data["lines"]
        voltages = data.get("voltages", {})
    else:
        raise ValueError("No network topology data found in data source")

    # Create graph
    G = nx.Graph()

    # Add edges from lines
    for line_info in lines:
        if isinstance(line_info, dict):
            bus1 = line_info["bus1"]
            bus2 = line_info["bus2"]
        else:
            # Handle tuple format
            bus1, bus2 = line_info[0], line_info[1]
        G.add_edge(bus1, bus2)

    # Create figure
    figsize = options.get("figsize", (14, 10))
    fig, ax = plt.subplots(figsize=figsize)

    # Layout
    pos = nx.spring_layout(G, seed=42, k=0.5, iterations=50)

    # Node colors based on voltage
    node_colors = []
    for node in G.nodes():
        if node in voltages:
            v = voltages[node]
            if v < 0.95 or v > 1.05:
                node_colors.append("red")
            elif v < 0.97 or v > 1.03:
                node_colors.append("orange")
            else:
                node_colors.append("lightgreen")
        else:
            node_colors.append("lightblue")

    # Draw network
    nx.draw_networkx_nodes(
        G,
        pos,
        node_color=node_colors,
        node_size=300,
        edgecolors="black",
        linewidths=1.5,
        ax=ax,
    )
    nx.draw_networkx_edges(G, pos, edge_color="gray", width=1.5, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight="bold", ax=ax)

    # Customize plot
    title = options.get("title", "Network Topology Diagram")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.axis("off")

    # Add legend
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor="lightgreen", edgecolor="black", label="Normal Voltage"),
        Patch(
            facecolor="orange",
            edgecolor="black",
            label="Warning (0.95-0.97 or 1.03-1.05 pu)",
        ),
        Patch(
            facecolor="red", edgecolor="black", label="Violation (<0.95 or >1.05 pu)"
        ),
    ]
    ax.legend(handles=legend_elements, loc="upper right")

    plt.tight_layout()
    return fig


def _plot_timeseries(data: dict[str, Any], options: dict) -> plt.Figure:
    """
    Create time-series line plots.

    Args:
        data: Data dictionary with time-series information
        options: Plot options

    Returns:
        Matplotlib figure
    """
    # Extract time-series data
    if "timesteps" in data:
        timesteps = data["timesteps"]
    elif "data" in data and "timesteps" in data["data"]:
        timesteps = data["data"]["timesteps"]
    else:
        raise ValueError("No time-series data found in data source")

    # Determine variables to plot
    variables = options.get("variables")
    if not variables:
        # Auto-detect available variables
        first_ts = timesteps[0]
        variables = [
            k for k in first_ts.keys() if k not in ["timestep", "hour", "converged"]
        ]
        # Limit to most common variables
        common_vars = ["total_load_kw", "losses_kw", "min_voltage_pu", "max_voltage_pu"]
        variables = [v for v in common_vars if v in variables]

    if not variables:
        raise ValueError("No plottable variables found in time-series data")

    # Extract hours and data for each variable
    hours = [ts["hour"] for ts in timesteps]

    # Create figure with subplots
    num_vars = len(variables)
    figsize = options.get("figsize", (12, 3 * num_vars))
    fig, axes = plt.subplots(num_vars, 1, figsize=figsize, sharex=True)

    if num_vars == 1:
        axes = [axes]

    # Plot each variable
    for i, var in enumerate(variables):
        ax = axes[i]
        values = [ts.get(var, 0) for ts in timesteps]

        # Plot line
        color = options.get("color", "steelblue")
        ax.plot(hours, values, color=color, linewidth=2, label=var)

        # Customize
        var_label = var.replace("_", " ").title()
        ax.set_ylabel(var_label, fontsize=11)
        ax.legend(loc="upper right")

        if options.get("show_grid", True):
            ax.grid(True, alpha=0.3, linestyle="--")

    # Overall title and xlabel
    title = options.get("title", "Time-Series Analysis")
    fig.suptitle(title, fontsize=14, fontweight="bold")

    xlabel = options.get("xlabel", "Hour")
    axes[-1].set_xlabel(xlabel, fontsize=12)

    plt.tight_layout()
    return fig


def _plot_capacity_curve(data: dict[str, Any], options: dict) -> plt.Figure:
    """
    Create capacity analysis scatter plot.

    Args:
        data: Data dictionary with capacity analysis results
        options: Plot options

    Returns:
        Matplotlib figure
    """
    # Extract capacity data - try multiple possible data structures
    results = None
    if "capacity_curve" in data:
        results = data["capacity_curve"]
    elif "data" in data and "capacity_curve" in data["data"]:
        results = data["data"]["capacity_curve"]
    elif "results" in data:
        results = data["results"]
    elif "data" in data and "results" in data["data"]:
        results = data["data"]["results"]
    else:
        raise ValueError("No capacity data found in data source")

    if not results or len(results) == 0:
        raise ValueError("Capacity curve data is empty")

    # Extract capacity and metric values
    capacities = [r["capacity_kw"] for r in results]
    metrics = [
        r.get("max_line_loading_pct", r.get("max_loading_pct", 0)) for r in results
    ]

    # Create figure
    figsize = options.get("figsize", (10, 6))
    fig, ax = plt.subplots(figsize=figsize)

    # Scatter plot
    color = options.get("color", "steelblue")
    ax.scatter(
        capacities,
        metrics,
        s=100,
        color=color,
        edgecolors="black",
        linewidths=1.5,
        alpha=0.7,
    )

    # Connect points with line
    ax.plot(capacities, metrics, color="gray", linewidth=1, alpha=0.5, linestyle="--")

    # Customize plot
    title = options.get("title", "Capacity Analysis Curve")
    xlabel = options.get("xlabel", "Capacity (kW)")
    ylabel = options.get("ylabel", "Maximum Loading (%)")

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)

    if options.get("show_grid", True):
        ax.grid(True, alpha=0.3, linestyle="--")

    plt.tight_layout()
    return fig


def _plot_harmonics_spectrum(data: dict[str, Any], options: dict) -> plt.Figure:
    """
    Create harmonics spectrum bar chart.

    Args:
        data: Data dictionary with harmonics information
        options: Plot options

    Returns:
        Matplotlib figure
    """
    # Extract harmonics data
    if "harmonics" in data:
        harmonics_dict = data["harmonics"]
    elif "data" in data and "harmonics" in data["data"]:
        harmonics_dict = data["data"]["harmonics"]
    else:
        raise ValueError("No harmonics data found in data source")

    # Apply bus filter
    bus_filter = options.get("bus_filter")
    if bus_filter:
        # Plot specific buses
        buses_to_plot = bus_filter
    else:
        # Plot worst THD bus
        if "worst_thd_bus" in harmonics_dict:
            buses_to_plot = [harmonics_dict["worst_thd_bus"]]
        else:
            # Use first available bus
            thd_voltage = harmonics_dict.get("thd_voltage", {})
            if thd_voltage:
                buses_to_plot = [list(thd_voltage.keys())[0]]
            else:
                raise ValueError("No bus harmonic data available")

    # Get individual harmonics data
    individual_harmonics = harmonics_dict.get("individual_harmonics", {})

    # Create figure
    num_buses = len(buses_to_plot)
    figsize = options.get("figsize", (12, 4 * num_buses))
    fig, axes = plt.subplots(num_buses, 1, figsize=figsize)

    if num_buses == 1:
        axes = [axes]

    # Plot each bus
    for i, bus_name in enumerate(buses_to_plot):
        ax = axes[i]

        # Get harmonic orders and magnitudes
        bus_harmonics = {}
        for order, buses_dict in individual_harmonics.items():
            if bus_name in buses_dict:
                bus_harmonics[int(order)] = buses_dict[bus_name]

        if not bus_harmonics:
            ax.text(
                0.5,
                0.5,
                f"No data for bus {bus_name}",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            continue

        orders = sorted(bus_harmonics.keys())
        magnitudes = [bus_harmonics[o] for o in orders]

        # Bar chart
        color = options.get("color", "steelblue")
        bars = ax.bar(orders, magnitudes, color=color, edgecolor="black", linewidth=0.5)

        # Highlight fundamental (order 1)
        if 1 in orders:
            idx = orders.index(1)
            bars[idx].set_color("green")

        # Customize
        ax.set_title(
            f"Harmonic Spectrum - Bus {bus_name}", fontsize=12, fontweight="bold"
        )
        ax.set_xlabel("Harmonic Order", fontsize=11)
        ax.set_ylabel("Magnitude (V or A)", fontsize=11)

        if options.get("show_grid", True):
            ax.grid(True, alpha=0.3, linestyle="--", axis="y")

        # Add THD annotation
        thd_voltage = harmonics_dict.get("thd_voltage", {})
        if bus_name in thd_voltage:
            thd = thd_voltage[bus_name]
            ax.text(
                0.95,
                0.95,
                f"THD: {thd:.2f}%",
                transform=ax.transAxes,
                fontsize=10,
                verticalalignment="top",
                horizontalalignment="right",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
            )

    # Overall title
    title = options.get("title", "Harmonics Analysis")
    fig.suptitle(title, fontsize=14, fontweight="bold")

    plt.tight_layout()
    return fig
