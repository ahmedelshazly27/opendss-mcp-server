"""
Performance benchmarks for OpenDSS MCP Server.

This module tests the performance of key operations to ensure they meet
the project's performance requirements.

Performance Targets:
- Power flow (IEEE123): < 5 seconds
- DER optimization (10 candidates): < 30 seconds
- Time-series simulation (24 hours): < 60 seconds
"""

import time
from typing import Any

from opendss_mcp.tools.feeder_loader import load_ieee_test_feeder
from opendss_mcp.tools.power_flow import run_power_flow
from opendss_mcp.tools.der_optimizer import optimize_der_placement
from opendss_mcp.tools.timeseries import run_time_series_simulation


def format_time(seconds: float) -> str:
    """Format time in seconds to human-readable string.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string
    """
    if seconds < 1:
        return f"{seconds * 1000:.2f} ms"
    elif seconds < 60:
        return f"{seconds:.2f} s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.2f}s"


def print_result(
    test_name: str,
    elapsed_time: float,
    target_time: float,
    success: bool,
    details: str = "",
) -> None:
    """Print formatted benchmark result.

    Args:
        test_name: Name of the benchmark test
        elapsed_time: Actual elapsed time
        target_time: Target time threshold
        success: Whether the operation succeeded
        details: Additional details to print
    """
    status = "✓ PASS" if elapsed_time < target_time and success else "✗ FAIL"
    print(f"\n{test_name}")
    print(f"  Time: {format_time(elapsed_time)} / {format_time(target_time)}")
    print(f"  Status: {status}")
    if details:
        print(f"  Details: {details}")


def test_power_flow_performance() -> dict[str, Any]:
    """Benchmark power flow analysis on IEEE123 (largest test feeder).

    Target: < 5 seconds

    Returns:
        Dictionary with test results
    """
    print("\n" + "=" * 70)
    print("BENCHMARK 1: Power Flow Analysis (IEEE123)")
    print("=" * 70)

    # Load feeder (not counted in performance time)
    print("Loading IEEE123 feeder...")
    load_result = load_ieee_test_feeder("IEEE123")
    if not load_result["success"]:
        print(f"  ✗ Failed to load feeder: {load_result.get('errors')}")
        return {
            "test": "power_flow",
            "success": False,
            "time": 0,
            "target": 5.0,
        }

    # Measure power flow time
    print("Running power flow analysis...")
    start_time = time.time()
    pf_result = run_power_flow("IEEE123")
    elapsed_time = time.time() - start_time

    success = pf_result["success"]
    details = ""
    if success:
        min_v = pf_result["data"]["min_voltage"]
        max_v = pf_result["data"]["max_voltage"]
        details = f"Voltage range: {min_v:.4f} - {max_v:.4f} pu"

    print_result(
        "Power Flow (IEEE123)",
        elapsed_time,
        target_time=5.0,
        success=success,
        details=details,
    )

    return {
        "test": "power_flow",
        "success": success,
        "time": elapsed_time,
        "target": 5.0,
        "passed": elapsed_time < 5.0 and success,
    }


def test_der_optimization_performance() -> dict[str, Any]:
    """Benchmark DER placement optimization with 10 candidates.

    Target: < 30 seconds

    Returns:
        Dictionary with test results
    """
    print("\n" + "=" * 70)
    print("BENCHMARK 2: DER Placement Optimization (10 candidates)")
    print("=" * 70)

    # Load feeder (not counted in performance time)
    print("Loading IEEE123 feeder...")
    load_result = load_ieee_test_feeder("IEEE123")
    if not load_result["success"]:
        print(f"  ✗ Failed to load feeder: {load_result.get('errors')}")
        return {
            "test": "der_optimization",
            "success": False,
            "time": 0,
            "target": 30.0,
        }

    # Run initial power flow (not counted)
    print("Running initial power flow...")
    run_power_flow("IEEE123")

    # Select 10 candidate buses from IEEE123
    # Using various buses spread throughout the feeder
    # These are load buses from the IEEE123 feeder
    candidate_buses = [
        "1",
        "7",
        "13",
        "18",
        "35",
        "40",
        "57",
        "60",
        "72",
        "97",
    ]

    # Measure optimization time
    print(f"Optimizing DER placement across {len(candidate_buses)} buses...")
    start_time = time.time()
    opt_result = optimize_der_placement(
        der_type="solar",
        capacity_kw=500,
        objective="minimize_losses",
        candidate_buses=candidate_buses,
    )
    elapsed_time = time.time() - start_time

    success = opt_result["success"]
    details = ""
    if success:
        optimal_bus = opt_result["data"]["optimal_bus"]
        loss_reduction = opt_result["data"]["improvement_metrics"]["loss_reduction_pct"]
        details = f"Optimal bus: {optimal_bus}, Loss reduction: {loss_reduction:.2f}%"
    else:
        # Print error for debugging
        error_msg = opt_result.get("errors", ["Unknown error"])[0]
        details = f"Error: {error_msg[:50]}"

    print_result(
        "DER Optimization (10 candidates)",
        elapsed_time,
        target_time=30.0,
        success=success,
        details=details,
    )

    return {
        "test": "der_optimization",
        "success": success,
        "time": elapsed_time,
        "target": 30.0,
        "passed": elapsed_time < 30.0 and success,
    }


def test_timeseries_performance() -> dict[str, Any]:
    """Benchmark 24-hour time-series simulation.

    Target: < 60 seconds

    Returns:
        Dictionary with test results
    """
    print("\n" + "=" * 70)
    print("BENCHMARK 3: Time-Series Simulation (24 hours)")
    print("=" * 70)

    # Load feeder (not counted in performance time)
    print("Loading IEEE13 feeder...")
    load_result = load_ieee_test_feeder("IEEE13")
    if not load_result["success"]:
        print(f"  ✗ Failed to load feeder: {load_result.get('errors')}")
        return {
            "test": "timeseries",
            "success": False,
            "time": 0,
            "target": 60.0,
        }

    # Create a simple flat load profile for 24 hours
    load_profile = {
        "name": "BENCHMARK_FLAT",
        "multipliers": [1.0] * 24,  # Constant load for 24 hours
    }

    # Measure time-series simulation
    print("Running 24-hour simulation (hourly steps)...")
    start_time = time.time()
    ts_result = run_time_series_simulation(
        load_profile=load_profile,
        duration_hours=24,
        timestep_minutes=60,  # Hourly
    )
    elapsed_time = time.time() - start_time

    success = ts_result["success"]
    details = ""
    if success:
        num_steps = ts_result["data"]["summary"]["num_timesteps"]
        avg_losses = ts_result["data"]["summary"].get("avg_losses_kw", 0)
        details = f"Steps: {num_steps}, Avg losses: {avg_losses:.2f} kW"

    print_result(
        "Time-Series Simulation (24h)",
        elapsed_time,
        target_time=60.0,
        success=success,
        details=details,
    )

    return {
        "test": "timeseries",
        "success": success,
        "time": elapsed_time,
        "target": 60.0,
        "passed": elapsed_time < 60.0 and success,
    }


def print_summary_table(results: list[dict[str, Any]]) -> None:
    """Print summary table of all benchmark results.

    Args:
        results: List of benchmark result dictionaries
    """
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)

    # Print table header
    print(f"\n{'Test':<30} {'Time':<15} {'Target':<15} {'Status':<10}")
    print("-" * 70)

    # Print each result
    for result in results:
        test_name = result["test"].replace("_", " ").title()
        time_str = format_time(result["time"])
        target_str = format_time(result["target"])
        status = "✓ PASS" if result["passed"] else "✗ FAIL"

        print(f"{test_name:<30} {time_str:<15} {target_str:<15} {status:<10}")

    # Print overall result
    print("-" * 70)
    all_passed = all(r["passed"] for r in results)
    total_time = sum(r["time"] for r in results)

    print(f"\nTotal execution time: {format_time(total_time)}")
    print(
        f"Overall status: {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}"
    )
    print()


def run_all_benchmarks() -> None:
    """Run all performance benchmarks and print summary."""
    print("\n" + "=" * 70)
    print("OpenDSS MCP Server - Performance Benchmarks")
    print("=" * 70)
    print("\nPerformance Targets:")
    print("  • Power Flow (IEEE123):        < 5 seconds")
    print("  • DER Optimization (10 buses): < 30 seconds")
    print("  • Time-Series (24 hours):      < 60 seconds")
    print()

    results = []

    # Run benchmarks
    try:
        results.append(test_power_flow_performance())
    except Exception as e:
        print(f"\n✗ Power flow benchmark failed with error: {e}")
        results.append(
            {
                "test": "power_flow",
                "success": False,
                "time": 0,
                "target": 5.0,
                "passed": False,
            }
        )

    try:
        results.append(test_der_optimization_performance())
    except Exception as e:
        print(f"\n✗ DER optimization benchmark failed with error: {e}")
        results.append(
            {
                "test": "der_optimization",
                "success": False,
                "time": 0,
                "target": 30.0,
                "passed": False,
            }
        )

    try:
        results.append(test_timeseries_performance())
    except Exception as e:
        print(f"\n✗ Time-series benchmark failed with error: {e}")
        results.append(
            {
                "test": "timeseries",
                "success": False,
                "time": 0,
                "target": 60.0,
                "passed": False,
            }
        )

    # Print summary
    print_summary_table(results)


if __name__ == "__main__":
    run_all_benchmarks()
