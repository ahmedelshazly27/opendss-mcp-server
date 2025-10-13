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
        required_fields = ["bus", "phase", "voltage_pu", "violation_type", "deviation_pu", "severity"]
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
        "worst_violation"
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
