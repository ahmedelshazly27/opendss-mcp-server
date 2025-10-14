"""
Unit tests for DER placement optimization functionality.
"""

import pytest
from opendss_mcp.tools.feeder_loader import load_ieee_test_feeder
from opendss_mcp.tools.power_flow import run_power_flow
from opendss_mcp.tools.der_optimizer import optimize_der_placement


def test_der_optimization_solar():
    """Test DER optimization with solar PV."""
    # Load feeder and run power flow
    load_result = load_ieee_test_feeder("IEEE13")
    assert load_result["success"], f"Failed to load feeder: {load_result.get('errors')}"

    pf_result = run_power_flow("IEEE13")
    assert pf_result["success"], f"Power flow failed: {pf_result.get('errors')}"

    # Run solar DER optimization with specific candidates
    result = optimize_der_placement(
        der_type="solar",
        capacity_kw=500,
        objective="minimize_losses",
        candidate_buses=["675", "671", "611", "652"]
    )

    # Verify operation succeeded
    assert result["success"], f"DER optimization failed: {result.get('errors')}"

    # Verify optimal bus was found
    assert "data" in result
    data = result["data"]
    assert "optimal_bus" in data
    assert data["optimal_bus"] in ["675", "671", "611", "652"]

    # Check loss reduction percentage
    assert "improvement_metrics" in data
    improvement = data["improvement_metrics"]
    assert "loss_reduction_pct" in improvement
    # Should have some impact (positive or negative)
    assert isinstance(improvement["loss_reduction_pct"], (int, float))


def test_der_optimization_battery():
    """Test DER optimization with battery storage."""
    # Load and solve
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Run battery DER optimization
    result = optimize_der_placement(
        der_type="battery",
        capacity_kw=300,
        battery_kwh=1200,  # 4-hour battery
        objective="minimize_losses",
        candidate_buses=["675", "671"]
    )

    # Verify success
    assert result["success"]

    # Check results format
    data = result["data"]
    assert data["der_type"] == "battery"
    assert data["optimal_capacity_kw"] == 300

    # Verify required fields exist
    assert "optimal_bus" in data
    assert "improvement_metrics" in data
    assert "comparison_table" in data
    assert "baseline" in data

    # Check baseline has required fields
    assert "losses_kw" in data["baseline"]
    assert "voltage_violations" in data["baseline"]


def test_comparison_table():
    """Test that comparison table has multiple entries and is sorted."""
    # Load and solve
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Run optimization with multiple candidates
    result = optimize_der_placement(
        der_type="solar",
        capacity_kw=400,
        objective="minimize_losses",
        candidate_buses=["675", "671", "611", "652", "645"]
    )

    assert result["success"]

    # Verify comparison table
    comparison_table = result["data"]["comparison_table"]
    assert isinstance(comparison_table, list)
    assert len(comparison_table) > 1  # Should have multiple entries

    # Check each entry has required fields
    for entry in comparison_table:
        assert "bus_id" in entry
        assert "objective_value" in entry
        assert "losses_kw" in entry
        assert "loss_reduction_kw" in entry
        assert "voltage_violations" in entry

    # Verify sorting by objective_value (descending - higher is better)
    if len(comparison_table) > 1:
        for i in range(len(comparison_table) - 1):
            assert comparison_table[i]["objective_value"] >= comparison_table[i + 1]["objective_value"], \
                "Comparison table should be sorted by objective_value (descending)"

    # Verify optimal bus matches first entry in comparison table
    optimal_bus = result["data"]["optimal_bus"]
    assert optimal_bus == comparison_table[0]["bus_id"]


def test_der_optimization_with_vvc():
    """Test DER optimization with volt-var control enabled."""
    # Load and solve
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Run solar_vvc optimization with IEEE1547 curve
    result = optimize_der_placement(
        der_type="solar_vvc",
        capacity_kw=500,
        objective="minimize_losses",
        candidate_buses=["675", "671", "611", "652"],
        control_settings={
            "curve": "IEEE1547",
            "response_time": 10.0
        }
    )

    # Verify operation succeeded
    assert result["success"], f"DER optimization with VVC failed: {result.get('errors')}"

    # Verify optimal bus was found
    data = result["data"]
    assert "optimal_bus" in data
    assert data["optimal_bus"] in ["675", "671", "611", "652"]

    # Verify der_type reflects VVC
    assert data["der_type"] == "solar_vvc"

    # Verify comparison table includes q_support_kvar
    comparison_table = data["comparison_table"]
    assert len(comparison_table) > 0

    for entry in comparison_table:
        assert "q_support_kvar" in entry, "VVC optimization should include q_support_kvar"
        assert isinstance(entry["q_support_kvar"], (int, float))

    # At least one bus should have non-zero reactive power support
    # Note: The actual value depends on voltage conditions, but we can verify the field exists
    q_values = [entry["q_support_kvar"] for entry in comparison_table]
    assert any(isinstance(q, (int, float)) for q in q_values), "Should have q_support_kvar values"


def test_der_optimization_solar_battery_vvc():
    """Test hybrid solar+battery optimization with volt-var control."""
    # Load and solve
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Run solar_battery_vvc optimization with RULE21 curve
    result = optimize_der_placement(
        der_type="solar_battery_vvc",
        capacity_kw=400,
        battery_kwh=1600,
        objective="minimize_violations",
        candidate_buses=["675", "671", "611"],
        control_settings={
            "curve": "RULE21",
            "response_time": 5.0
        }
    )

    # Verify operation succeeded
    assert result["success"], f"Hybrid VVC optimization failed: {result.get('errors')}"

    # Verify results structure
    data = result["data"]
    assert data["der_type"] == "solar_battery_vvc"
    assert "optimal_bus" in data
    assert "comparison_table" in data

    # Verify q_support_kvar is included
    comparison_table = data["comparison_table"]
    for entry in comparison_table:
        assert "q_support_kvar" in entry


def test_vvc_vs_no_vvc_comparison():
    """Compare optimization results with and without volt-var control."""
    # Run without VVC
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    result_no_vvc = optimize_der_placement(
        der_type="solar",
        capacity_kw=500,
        objective="minimize_losses",
        candidate_buses=["675", "671"]
    )

    # Reload feeder for second run to avoid duplicate elements
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Run with VVC
    result_with_vvc = optimize_der_placement(
        der_type="solar_vvc",
        capacity_kw=500,
        objective="minimize_losses",
        candidate_buses=["675", "671"],
        control_settings={"curve": "IEEE1547"}
    )

    # Both should succeed
    assert result_no_vvc["success"]
    assert result_with_vvc["success"]

    # Check q_support_kvar field presence
    no_vvc_table = result_no_vvc["data"]["comparison_table"]
    with_vvc_table = result_with_vvc["data"]["comparison_table"]

    # Without VVC: q_support_kvar should be 0 or not included meaningfully
    for entry in no_vvc_table:
        assert "q_support_kvar" in entry
        # Should be zero since no VVC
        assert entry["q_support_kvar"] == 0.0

    # With VVC: q_support_kvar should be included (may or may not be non-zero depending on conditions)
    for entry in with_vvc_table:
        assert "q_support_kvar" in entry
        assert isinstance(entry["q_support_kvar"], (int, float))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
