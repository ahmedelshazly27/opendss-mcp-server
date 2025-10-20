"""
Generate example plots demonstrating the visualization tool.

This script demonstrates all 5 visualization types supported by the OpenDSS MCP Server:
1. Voltage Profile - Bar chart of bus voltages
2. Network Diagram - Network topology with networkx
3. Time-Series - Line plots over time (simulated)
4. Capacity Curve - DER hosting capacity analysis
5. Harmonics Spectrum - Harmonic voltage magnitudes

All plots are saved to the examples/plots/ directory.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from opendss_mcp.tools.feeder_loader import load_ieee_test_feeder
from opendss_mcp.tools.power_flow import run_power_flow
from opendss_mcp.tools.voltage_checker import check_voltage_violations
from opendss_mcp.tools.capacity import analyze_feeder_capacity
from opendss_mcp.tools.visualization import (
    generate_visualization,
    store_visualization_data,
)


def setup_output_directory():
    """Create the plots directory if it doesn't exist."""
    plots_dir = Path(__file__).parent / "plots"
    plots_dir.mkdir(exist_ok=True)
    return plots_dir


def generate_voltage_profile(plots_dir: Path):
    """Generate voltage profile visualization."""
    print("\n" + "=" * 70)
    print("1. VOLTAGE PROFILE VISUALIZATION")
    print("=" * 70)

    print("\nLoading IEEE13 feeder...")
    load_result = load_ieee_test_feeder("IEEE13")
    if not load_result["success"]:
        print(f"❌ Failed to load feeder: {load_result['errors']}")
        return False
    print("✓ Feeder loaded")

    print("Running power flow...")
    pf_result = run_power_flow("IEEE13")
    if not pf_result["success"]:
        print(f"❌ Failed to run power flow: {pf_result['errors']}")
        return False
    print("✓ Power flow converged")

    # Store data for visualization
    store_visualization_data("power_flow", pf_result)

    print("Generating voltage profile plot...")
    save_path = plots_dir / "01_voltage_profile.png"
    viz_result = generate_visualization(
        plot_type="voltage_profile",
        data_source="circuit",
        options={
            "save_path": str(save_path),
            "title": "IEEE 13 Bus Voltage Profile",
            "figsize": (14, 6),
            "dpi": 150,
            "show_violations": True,
        },
    )

    if not viz_result["success"]:
        print(f"❌ Failed: {viz_result['errors']}")
        return False

    print(f"✓ Saved to: {save_path}")
    return True


def generate_network_diagram(plots_dir: Path):
    """Generate network topology diagram."""
    print("\n" + "=" * 70)
    print("2. NETWORK DIAGRAM VISUALIZATION")
    print("=" * 70)

    print("\nGenerating network diagram...")
    save_path = plots_dir / "02_network_diagram.png"
    viz_result = generate_visualization(
        plot_type="network_diagram",
        data_source="circuit",
        options={
            "save_path": str(save_path),
            "title": "IEEE 13 Bus Network Topology",
            "figsize": (14, 10),
            "dpi": 150,
            "layout": "spring",
        },
    )

    if not viz_result["success"]:
        print(f"❌ Failed: {viz_result['errors']}")
        return False

    print(f"✓ Saved to: {save_path}")
    return True


def generate_timeseries_plot(plots_dir: Path):
    """Generate time-series visualization with simulated data."""
    print("\n" + "=" * 70)
    print("3. TIME-SERIES VISUALIZATION")
    print("=" * 70)

    print("\nCreating simulated time-series data...")
    # Simulate a 24-hour load curve
    import numpy as np

    hours = list(range(24))
    base_load = 5000  # kW
    load_profile = [
        base_load * (0.6 + 0.4 * np.sin((h - 6) * np.pi / 12)) for h in hours
    ]
    losses = [load * 0.03 for load in load_profile]  # 3% losses
    min_voltages = [
        0.98 - 0.02 * (load / base_load - 0.6) / 0.4 for load in load_profile
    ]
    max_voltages = [
        1.02 + 0.01 * (load / base_load - 0.6) / 0.4 for load in load_profile
    ]

    # Create time-series data structure
    timesteps = []
    for i, hour in enumerate(hours):
        timesteps.append(
            {
                "timestep": i,
                "hour": hour,
                "total_load_kw": load_profile[i],
                "losses_kw": losses[i],
                "min_voltage_pu": min_voltages[i],
                "max_voltage_pu": max_voltages[i],
                "converged": True,
            }
        )

    timeseries_data = {"data": {"timesteps": timesteps}}

    # Store for visualization
    store_visualization_data("timeseries", timeseries_data)

    print("Generating time-series plot...")
    save_path = plots_dir / "03_timeseries.png"
    viz_result = generate_visualization(
        plot_type="timeseries",
        data_source="last_timeseries",
        options={
            "save_path": str(save_path),
            "title": "24-Hour Load Profile Analysis",
            "figsize": (14, 8),
            "dpi": 150,
            "variables": [
                "total_load_kw",
                "losses_kw",
                "min_voltage_pu",
                "max_voltage_pu",
            ],
        },
    )

    if not viz_result["success"]:
        print(f"❌ Failed: {viz_result['errors']}")
        return False

    print(f"✓ Saved to: {save_path}")
    return True


def generate_capacity_curve(plots_dir: Path):
    """Generate capacity curve visualization."""
    print("\n" + "=" * 70)
    print("4. CAPACITY CURVE VISUALIZATION")
    print("=" * 70)

    print("\nAnalyzing hosting capacity at bus 675...")
    # Run capacity analysis
    capacity_result = analyze_feeder_capacity(
        bus_id="675",
        der_type="solar",
        increment_kw=200,
        max_capacity_kw=2000,
        constraints={"max_voltage_pu": 1.05},
    )

    if not capacity_result["success"]:
        print(f"❌ Failed to analyze capacity: {capacity_result['errors']}")
        return False

    max_capacity = capacity_result["data"]["max_capacity_kw"]
    print(f"✓ Max capacity: {max_capacity} kW")

    # Store for visualization
    store_visualization_data("capacity", capacity_result)

    print("Generating capacity curve plot...")
    save_path = plots_dir / "04_capacity_curve.png"
    viz_result = generate_visualization(
        plot_type="capacity_curve",
        data_source="last_capacity",
        options={
            "save_path": str(save_path),
            "title": "DER Hosting Capacity Analysis - Bus 675",
            "figsize": (12, 6),
            "dpi": 150,
            "xlabel": "DER Capacity (kW)",
            "ylabel": "Maximum Line Loading (%)",
        },
    )

    if not viz_result["success"]:
        print(f"❌ Failed: {viz_result['errors']}")
        return False

    print(f"✓ Saved to: {save_path}")
    return True


def generate_harmonics_spectrum(plots_dir: Path):
    """Generate harmonics spectrum visualization."""
    print("\n" + "=" * 70)
    print("5. HARMONICS SPECTRUM VISUALIZATION")
    print("=" * 70)

    print("\nRunning power flow with harmonics analysis...")
    pf_result = run_power_flow(
        "IEEE13",
        options={"harmonic_analysis": True, "harmonic_orders": [1, 3, 5, 7, 9, 11, 13]},
    )

    if not pf_result["success"]:
        print(f"❌ Failed to run power flow: {pf_result['errors']}")
        return False

    if "harmonics" not in pf_result["data"]:
        print("⚠️  No harmonics data available (may need harmonic sources in circuit)")
        print("Creating simulated harmonics data for demonstration...")

        # Create simulated harmonics data
        import numpy as np

        buses = ["650", "632", "671", "692", "675"]
        harmonics_data = {
            "data": {
                "harmonics": {
                    "individual_harmonics": {},
                    "thd_voltage": {},
                    "worst_thd_bus": "671",
                    "worst_thd_value": 3.2,
                }
            }
        }

        # Simulate harmonic voltages (fundamental + harmonics)
        for order in [1, 3, 5, 7, 9, 11, 13]:
            harmonics_data["data"]["harmonics"]["individual_harmonics"][order] = {}
            for bus in buses:
                if order == 1:
                    # Fundamental is close to 1.0 pu
                    harmonics_data["data"]["harmonics"]["individual_harmonics"][order][
                        bus
                    ] = 0.98 + np.random.uniform(-0.02, 0.02)
                else:
                    # Higher harmonics are much smaller
                    harmonics_data["data"]["harmonics"]["individual_harmonics"][order][
                        bus
                    ] = (0.001 * (13 / order) * np.random.uniform(0.5, 1.5))

        # Calculate THD
        for bus in buses:
            thd = np.random.uniform(1.5, 4.0)
            harmonics_data["data"]["harmonics"]["thd_voltage"][bus] = thd

        store_visualization_data("harmonics", harmonics_data)
    else:
        print("✓ Harmonics analysis complete")
        store_visualization_data("harmonics", pf_result)

    print("Generating harmonics spectrum plot...")
    save_path = plots_dir / "05_harmonics_spectrum.png"
    viz_result = generate_visualization(
        plot_type="harmonics_spectrum",
        data_source="last_harmonics",
        options={
            "save_path": str(save_path),
            "title": "Harmonic Voltage Spectrum",
            "figsize": (12, 8),
            "dpi": 150,
            "bus_filter": ["650", "671", "675"],  # Show 3 representative buses
        },
    )

    if not viz_result["success"]:
        print(f"❌ Failed: {viz_result['errors']}")
        return False

    print(f"✓ Saved to: {save_path}")
    return True


def main():
    """Generate all example plots."""
    print("\n" + "=" * 70)
    print("OPENDSS MCP SERVER - VISUALIZATION EXAMPLES")
    print("=" * 70)
    print("\nThis script demonstrates all 5 visualization types by:")
    print("  1. Loading IEEE 13 Bus test feeder")
    print("  2. Running power flow analysis")
    print("  3. Performing capacity analysis")
    print("  4. Generating various plot types")
    print("  5. Saving all plots to examples/plots/")

    # Setup output directory
    plots_dir = setup_output_directory()
    print(f"\nOutput directory: {plots_dir.absolute()}")

    # Track results
    results = []

    # Generate all visualizations
    results.append(("Voltage Profile", generate_voltage_profile(plots_dir)))
    results.append(("Network Diagram", generate_network_diagram(plots_dir)))
    results.append(("Time-Series", generate_timeseries_plot(plots_dir)))
    results.append(("Capacity Curve", generate_capacity_curve(plots_dir)))
    results.append(("Harmonics Spectrum", generate_harmonics_spectrum(plots_dir)))

    # Print summary
    print("\n" + "=" * 70)
    print("GENERATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for i, (plot_name, result) in enumerate(results, 1):
        status = "✓ SUCCESS" if result else "❌ FAILED"
        filename = f"0{i}_{plot_name.lower().replace(' ', '_').replace('-', '_')}.png"
        print(f"{plot_name:20} {status:12} → {filename}")

    print("\n" + "-" * 70)
    print(f"Generated {passed}/{total} plots successfully")
    print(f"Location: {plots_dir.absolute()}")
    print("=" * 70)

    if passed == total:
        print("\n✓ All visualizations generated successfully!")
        print("\nYou can now view the plots in the examples/plots/ directory.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} visualization(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
