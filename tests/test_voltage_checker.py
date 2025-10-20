"""
Unit tests for voltage violation checking functionality.
"""

import pytest
from opendss_mcp.tools.feeder_loader import load_ieee_test_feeder
from opendss_mcp.tools.power_flow import run_power_flow
from opendss_mcp.tools.voltage_checker import check_voltage_violations


def test_no_violations():
    """Test voltage checker with default limits - just verify format."""
    # Load feeder and run power flow
    load_result = load_ieee_test_feeder("IEEE13")
    assert load_result["success"], f"Failed to load feeder: {load_result.get('errors')}"

    pf_result = run_power_flow("IEEE13")
    assert pf_result["success"], f"Power flow failed: {pf_result.get('errors')}"

    # Check for voltage violations with default limits
    result = check_voltage_violations()

    # Verify operation succeeded
    assert result["success"], f"Voltage check failed: {result.get('errors')}"

    # Verify data structure (may or may not have violations)
    assert "data" in result
    assert "violations" in result["data"]
    assert isinstance(result["data"]["violations"], list)

    # Verify summary exists
    assert "summary" in result["data"]
    summary = result["data"]["summary"]
    assert "total_violations" in summary
    assert "undervoltage_count" in summary
    assert "overvoltage_count" in summary
    assert "severity_counts" in summary

    # Total should equal undervoltage + overvoltage
    assert summary["total_violations"] == (
        summary["undervoltage_count"] + summary["overvoltage_count"]
    )


def test_strict_limits():
    """Test voltage checker with very strict limits - should detect violations."""
    # Load and solve
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Check with very strict limits (0.99-1.01)
    result = check_voltage_violations(min_voltage_pu=0.99, max_voltage_pu=1.01)

    assert result["success"]

    # With strict limits, should have violations
    assert result["data"]["summary"]["total_violations"] > 0

    # Verify violations have required fields
    for violation in result["data"]["violations"]:
        assert "bus" in violation
        assert "phase" in violation
        assert "voltage_pu" in violation
        assert "violation_type" in violation
        assert "deviation_pu" in violation
        assert "severity" in violation


def test_return_format():
    """Test that return format has all required fields."""
    # Load and solve
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Run check
    result = check_voltage_violations(min_voltage_pu=0.98, max_voltage_pu=1.02)

    # Check top-level structure
    assert "success" in result
    assert "data" in result
    assert "metadata" in result
    assert "errors" in result

    # Check data structure
    data = result["data"]
    assert "violations" in data
    assert "summary" in data
    assert "limits" in data
    assert "total_buses_checked" in data

    # Check violations structure (if any exist)
    if data["violations"]:
        violation = data["violations"][0]
        required_fields = [
            "bus",
            "phase",
            "voltage_pu",
            "violation_type",
            "deviation_pu",
            "severity",
        ]
        for field in required_fields:
            assert field in violation

        # Check violation_type is valid
        assert violation["violation_type"] in ["undervoltage", "overvoltage"]

        # Check severity is valid
        assert violation["severity"] in ["minor", "moderate", "severe"]

    # Check summary structure
    summary = data["summary"]
    required_summary_fields = [
        "total_violations",
        "undervoltage_count",
        "overvoltage_count",
        "severity_counts",
        "worst_violation",
    ]
    for field in required_summary_fields:
        assert field in summary

    # Check severity counts
    severity_counts = summary["severity_counts"]
    assert "minor" in severity_counts
    assert "moderate" in severity_counts
    assert "severe" in severity_counts

    # Check limits
    limits = data["limits"]
    assert "min_voltage_pu" in limits
    assert "max_voltage_pu" in limits
    assert "phase_filter" in limits

    # Check metadata
    metadata = result["metadata"]
    assert "circuit_name" in metadata
    assert "analysis_type" in metadata


def test_invalid_phase_filter():
    """Test voltage checker with invalid phase filter."""
    # Load and solve
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Check with invalid phase
    result = check_voltage_violations(phase="4")  # Invalid phase

    # Should fail
    assert result["success"] is False
    assert len(result["errors"]) > 0
    assert "invalid phase" in result["errors"][0].lower()


def test_phase_filter_specific_phase():
    """Test voltage checker with specific phase filter."""
    # Load and solve
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Check only phase 1 with strict limits
    result = check_voltage_violations(
        min_voltage_pu=0.99, max_voltage_pu=1.01, phase="1"
    )

    assert result["success"]

    # Verify phase filter is set
    assert result["data"]["limits"]["phase_filter"] == "1"

    # All violations should be for phase 1 only
    for violation in result["data"]["violations"]:
        assert violation["phase"] == "1"


def test_no_circuit_loaded():
    """Test voltage checker when no circuit is loaded."""
    import opendssdirect as dss

    # Clear circuit
    dss.Text.Command("Clear")

    # Try to check violations
    result = check_voltage_violations()

    # Should fail
    assert result["success"] is False
    assert len(result["errors"]) > 0
    # Check for circuit-related error message
    assert (
        "no circuit" in result["errors"][0].lower()
        or "active circuit" in result["errors"][0].lower()
    )


def test_no_voltage_data():
    """Test voltage checker when circuit is loaded but no power flow run."""
    import opendssdirect as dss

    # Load feeder but don't run power flow
    load_ieee_test_feeder("IEEE13")

    # The circuit is loaded, but _get_bus_voltages_by_phase might return empty
    # This tests the edge case handling
    result = check_voltage_violations()

    # Should either succeed with no violations or return error about no voltage data
    assert "success" in result
    # If it fails, should mention voltage data
    if not result["success"]:
        assert any("voltage data" in str(e).lower() for e in result["errors"])


def test_empty_voltage_bus():
    """Test _get_bus_voltages_by_phase with buses that have no voltage data."""
    # This is an internal function test through the public API
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Should handle buses with no voltage data gracefully
    result = check_voltage_violations()
    assert result["success"]


def test_voltage_limits_validation():
    """Test voltage checker with invalid voltage limits."""
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Test with invalid limits (min > max)
    result = check_voltage_violations(min_voltage_pu=1.05, max_voltage_pu=0.95)

    # Should fail due to validation error
    assert result["success"] is False
    assert len(result["errors"]) > 0


def test_severity_classification():
    """Test that violations are correctly classified by severity."""
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Use very wide limits first to see baseline, then narrow
    # Test with very strict limits to force violations
    result = check_voltage_violations(min_voltage_pu=0.98, max_voltage_pu=1.02)

    assert result["success"]

    if result["data"]["violations"]:
        # Verify severity counts add up
        severity_counts = result["data"]["summary"]["severity_counts"]
        total = (
            severity_counts["minor"]
            + severity_counts["moderate"]
            + severity_counts["severe"]
        )
        assert total == result["data"]["summary"]["total_violations"]

        # Verify each violation has valid severity
        for violation in result["data"]["violations"]:
            assert violation["severity"] in ["minor", "moderate", "severe"]

            # Check severity logic based on deviation
            abs_dev = abs(violation["deviation_pu"])
            if abs_dev < 0.02:
                assert violation["severity"] == "minor"
            elif abs_dev < 0.05:
                assert violation["severity"] == "moderate"
            else:
                assert violation["severity"] == "severe"


def test_worst_violation_identification():
    """Test that worst violation is correctly identified."""
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Use strict limits to get violations
    result = check_voltage_violations(min_voltage_pu=0.99, max_voltage_pu=1.01)

    assert result["success"]

    if result["data"]["summary"]["total_violations"] > 0:
        worst = result["data"]["summary"]["worst_violation"]
        assert worst is not None

        # Worst violation should be first in sorted list
        assert worst == result["data"]["violations"][0]

        # Verify it has largest absolute deviation
        abs_worst_dev = abs(worst["deviation_pu"])
        for violation in result["data"]["violations"]:
            assert abs(violation["deviation_pu"]) <= abs_worst_dev


def test_undervoltage_vs_overvoltage():
    """Test that undervoltage and overvoltage are correctly classified."""
    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Use strict limits
    result = check_voltage_violations(min_voltage_pu=0.99, max_voltage_pu=1.01)

    assert result["success"]

    # Verify violation types are correct
    for violation in result["data"]["violations"]:
        if violation["violation_type"] == "undervoltage":
            assert violation["voltage_pu"] < 0.99
            assert violation["deviation_pu"] < 0
        elif violation["violation_type"] == "overvoltage":
            assert violation["voltage_pu"] > 1.01
            assert violation["deviation_pu"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
