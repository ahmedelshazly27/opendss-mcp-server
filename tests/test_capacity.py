"""
Unit tests for capacity analysis functionality.
"""

import pytest
from opendss_mcp.tools.feeder_loader import load_ieee_test_feeder
from opendss_mcp.tools.power_flow import run_power_flow
from opendss_mcp.tools.capacity import analyze_feeder_capacity


def test_basic_capacity_analysis():
    """Test basic capacity analysis functionality."""
    # Load feeder and run power flow
    load_result = load_ieee_test_feeder("IEEE13")
    assert load_result["success"], f"Failed to load feeder: {load_result.get('errors')}"

    pf_result = run_power_flow("IEEE13")
    assert pf_result["success"], f"Power flow failed: {pf_result.get('errors')}"

    # Run capacity analysis on a bus
    result = analyze_feeder_capacity(
        bus_id="675",
        der_type="solar",
        increment_kw=100,
        max_capacity_kw=2000
    )

    # Verify operation succeeded
    assert result["success"], f"Capacity analysis failed: {result.get('errors')}"

    # Verify data structure
    assert "data" in result
    data = result["data"]

    assert "bus_id" in data
    assert "der_type" in data
    assert "max_capacity_kw" in data
    assert "limiting_constraint" in data
    assert "capacity_curve" in data
    assert "baseline" in data
    assert "constraints" in data
    assert "analysis_parameters" in data

    # Verify max capacity is non-negative
    assert data["max_capacity_kw"] >= 0


def test_capacity_with_constraints():
    """Test capacity analysis with custom constraints."""
    # Load and solve
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Run with strict voltage constraints
    constraints = {
        "min_voltage_pu": 0.98,
        "max_voltage_pu": 1.02,
        "max_line_loading_pct": 90.0
    }

    result = analyze_feeder_capacity(
        bus_id="675",
        der_type="solar",
        increment_kw=50,
        max_capacity_kw=1500,
        constraints=constraints
    )

    assert result["success"]

    # Verify constraints were applied
    assert result["data"]["constraints"]["min_voltage_pu"] == 0.98
    assert result["data"]["constraints"]["max_voltage_pu"] == 1.02
    assert result["data"]["constraints"]["max_line_loading_pct"] == 90.0


def test_return_format():
    """Test that return format has all required fields."""
    # Load and solve
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Run capacity analysis
    result = analyze_feeder_capacity(
        bus_id="675",
        der_type="solar",
        increment_kw=100,
        max_capacity_kw=1000
    )

    # Check top-level structure
    assert "success" in result
    assert "data" in result
    assert "metadata" in result
    assert "errors" in result

    # Check data structure
    data = result["data"]
    required_fields = [
        "bus_id",
        "der_type",
        "max_capacity_kw",
        "limiting_constraint",
        "violation_details",
        "capacity_curve",
        "baseline",
        "constraints",
        "analysis_parameters"
    ]

    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Check capacity curve structure
    assert isinstance(data["capacity_curve"], list)
    if data["capacity_curve"]:
        curve_point = data["capacity_curve"][0]
        assert "capacity_kw" in curve_point
        assert "converged" in curve_point
        assert "voltage_violations" in curve_point
        assert "max_line_loading_pct" in curve_point
        assert "has_violations" in curve_point

    # Check baseline structure
    baseline = data["baseline"]
    assert "voltage_violations" in baseline
    assert "max_line_loading_pct" in baseline

    # Check constraints structure
    constraints = data["constraints"]
    assert "min_voltage_pu" in constraints
    assert "max_voltage_pu" in constraints
    assert "max_line_loading_pct" in constraints

    # Check analysis parameters
    params = data["analysis_parameters"]
    assert "increment_kw" in params
    assert "max_capacity_tested_kw" in params
    assert "iterations_performed" in params

    # Check metadata
    metadata = result["metadata"]
    assert "circuit_name" in metadata
    assert "analysis_type" in metadata
    assert metadata["analysis_type"] == "hosting_capacity"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
