"""
Unit tests for harmonic analysis functionality.
"""

import pytest
from opendss_mcp.utils.harmonics import calculate_thd
from opendss_mcp.tools.feeder_loader import load_ieee_test_feeder
from opendss_mcp.tools.power_flow import run_power_flow


def test_thd_calculation():
    """Test THD calculation with known values.

    THD formula: THD = sqrt(sum(H_n^2 for n > 1)) / H_1 * 100

    Example:
        Given harmonics: {1: 120.0, 3: 10.0, 5: 8.0, 7: 5.0}
        Sum of squares = 10^2 + 8^2 + 5^2 = 100 + 64 + 25 = 189
        sqrt(189) = 13.7477...
        THD = (13.7477 / 120.0) * 100 = 11.4564...%
    """
    # Test case 1: Normal harmonics
    harmonics = {
        1: 120.0,  # Fundamental
        3: 10.0,   # 3rd harmonic
        5: 8.0,    # 5th harmonic
        7: 5.0     # 7th harmonic
    }

    thd = calculate_thd(harmonics)

    # Expected: sqrt(100 + 64 + 25) / 120 * 100 = sqrt(189) / 120 * 100
    # = 13.7477... / 120 * 100 = 11.4564...%
    expected_thd = 11.4564

    assert isinstance(thd, float), "THD should be a float"
    assert thd > 0, "THD should be positive"
    assert abs(thd - expected_thd) < 0.01, f"Expected THD ~{expected_thd}%, got {thd}%"


def test_thd_calculation_no_fundamental():
    """Test THD calculation when fundamental is missing."""
    harmonics = {
        3: 10.0,
        5: 8.0,
        7: 5.0
    }

    thd = calculate_thd(harmonics)

    # Should return 0.0 when fundamental is missing
    assert thd == 0.0, "THD should be 0.0 when fundamental is missing"


def test_thd_calculation_zero_fundamental():
    """Test THD calculation when fundamental is zero."""
    harmonics = {
        1: 0.0,  # Zero fundamental
        3: 10.0,
        5: 8.0
    }

    thd = calculate_thd(harmonics)

    # Should return 0.0 when fundamental is zero
    assert thd == 0.0, "THD should be 0.0 when fundamental is zero"


def test_thd_calculation_only_fundamental():
    """Test THD calculation with only fundamental (no harmonics)."""
    harmonics = {
        1: 120.0  # Only fundamental
    }

    thd = calculate_thd(harmonics)

    # Should return 0.0 when no harmonics above fundamental
    assert thd == 0.0, "THD should be 0.0 when only fundamental is present"


def test_thd_calculation_high_distortion():
    """Test THD calculation with high distortion."""
    harmonics = {
        1: 100.0,   # Fundamental
        3: 50.0,    # Large 3rd harmonic
        5: 30.0,    # Large 5th harmonic
        7: 20.0,    # Large 7th harmonic
        9: 10.0     # 9th harmonic
    }

    thd = calculate_thd(harmonics)

    # Expected: sqrt(2500 + 900 + 400 + 100) / 100 * 100
    # = sqrt(3900) / 100 * 100 = 62.45%
    expected_thd = 62.45

    assert thd > 50, "THD should be high for this test case"
    assert abs(thd - expected_thd) < 0.1, f"Expected THD ~{expected_thd}%, got {thd}%"


def test_power_flow_with_harmonics():
    """Test power flow analysis with harmonic analysis enabled.

    Note: This test may not produce meaningful harmonic results since the
    IEEE13 feeder doesn't have harmonic sources defined by default. However,
    it verifies that the harmonic analysis infrastructure works correctly.
    """
    # Load IEEE13 feeder
    load_result = load_ieee_test_feeder("IEEE13")
    assert load_result["success"], f"Failed to load feeder: {load_result.get('errors')}"

    # Run power flow with harmonic analysis enabled
    pf_result = run_power_flow("IEEE13", {
        "harmonic_analysis": True,
        "harmonic_orders": [1, 3, 5, 7]
    })

    # Verify operation succeeded
    assert pf_result["success"], f"Power flow failed: {pf_result.get('errors')}"

    # Verify basic power flow data exists
    assert "data" in pf_result
    data = pf_result["data"]
    assert data["converged"], "Power flow should converge"
    assert "bus_voltages" in data

    # Verify harmonics field exists
    assert "harmonics" in data, "Harmonics field should be present when harmonic_analysis=True"
    harmonics = data["harmonics"]

    # Verify harmonics structure
    assert "thd_voltage" in harmonics, "harmonics should contain thd_voltage"
    assert "thd_current" in harmonics, "harmonics should contain thd_current"
    assert "individual_harmonics" in harmonics, "harmonics should contain individual_harmonics"
    assert "worst_thd_bus" in harmonics, "harmonics should contain worst_thd_bus"
    assert "worst_thd_value" in harmonics, "harmonics should contain worst_thd_value"

    # Verify thd_voltage is a dictionary
    assert isinstance(harmonics["thd_voltage"], dict), "thd_voltage should be a dictionary"

    # Verify thd_current is a dictionary
    assert isinstance(harmonics["thd_current"], dict), "thd_current should be a dictionary"

    # Verify individual_harmonics structure
    assert isinstance(harmonics["individual_harmonics"], dict), "individual_harmonics should be a dictionary"

    # Verify individual harmonics contains the requested orders
    for order in [1, 3, 5, 7]:
        assert order in harmonics["individual_harmonics"], f"Harmonic order {order} should be in individual_harmonics"
        assert isinstance(harmonics["individual_harmonics"][order], dict), f"Order {order} should map to a dictionary"

    # Verify worst_thd_bus is a string
    assert isinstance(harmonics["worst_thd_bus"], str), "worst_thd_bus should be a string"

    # Verify worst_thd_value is a number
    assert isinstance(harmonics["worst_thd_value"], (int, float)), "worst_thd_value should be a number"
    assert harmonics["worst_thd_value"] >= 0, "worst_thd_value should be non-negative"

    # Verify options reflect harmonic analysis settings
    assert data["options"]["harmonic_analysis"] is True
    assert data["options"]["harmonic_orders"] == [1, 3, 5, 7]


def test_power_flow_with_harmonics_default_orders():
    """Test power flow with harmonics using default harmonic orders."""
    # Load IEEE13 feeder
    load_result = load_ieee_test_feeder("IEEE13")
    assert load_result["success"], f"Failed to load feeder: {load_result.get('errors')}"

    # Run power flow with harmonic analysis but no explicit orders
    pf_result = run_power_flow("IEEE13", {
        "harmonic_analysis": True
    })

    # Verify operation succeeded
    assert pf_result["success"], f"Power flow failed: {pf_result.get('errors')}"

    # Verify harmonics field exists
    data = pf_result["data"]
    assert "harmonics" in data

    # Verify default orders were used [1, 3, 5, 7, 9, 11, 13]
    default_orders = [1, 3, 5, 7, 9, 11, 13]
    assert data["options"]["harmonic_orders"] == default_orders

    # Verify individual harmonics contains all default orders
    individual_harmonics = data["harmonics"]["individual_harmonics"]
    for order in default_orders:
        assert order in individual_harmonics, f"Default harmonic order {order} should be present"


def test_harmonics_disabled():
    """Test that harmonics field is not present when harmonic analysis is disabled."""
    # Load IEEE13 feeder
    load_result = load_ieee_test_feeder("IEEE13")
    assert load_result["success"], f"Failed to load feeder: {load_result.get('errors')}"

    # Run power flow with harmonic analysis explicitly disabled
    pf_result = run_power_flow("IEEE13", {
        "harmonic_analysis": False
    })

    # Verify operation succeeded
    assert pf_result["success"], f"Power flow failed: {pf_result.get('errors')}"

    # Verify basic power flow data exists
    assert "data" in pf_result
    data = pf_result["data"]
    assert data["converged"], "Power flow should converge"

    # Verify harmonics field does NOT exist
    assert "harmonics" not in data, "Harmonics field should not be present when harmonic_analysis=False"

    # Verify options show harmonic analysis is disabled
    assert "harmonic_analysis" not in data["options"] or data["options"].get("harmonic_analysis") is False


def test_harmonics_disabled_by_default():
    """Test that harmonics are disabled by default (backward compatibility)."""
    # Load IEEE13 feeder
    load_result = load_ieee_test_feeder("IEEE13")
    assert load_result["success"], f"Failed to load feeder: {load_result.get('errors')}"

    # Run power flow without specifying harmonic options (default behavior)
    pf_result = run_power_flow("IEEE13")

    # Verify operation succeeded
    assert pf_result["success"], f"Power flow failed: {pf_result.get('errors')}"

    # Verify harmonics field does NOT exist (backward compatibility)
    assert "data" in pf_result
    data = pf_result["data"]
    assert "harmonics" not in data, "Harmonics should be disabled by default for backward compatibility"


def test_harmonics_structure_complete():
    """Test that harmonic analysis returns the complete expected structure."""
    # Load IEEE13 feeder
    load_result = load_ieee_test_feeder("IEEE13")
    assert load_result["success"], f"Failed to load feeder: {load_result.get('errors')}"

    # Run power flow with harmonics
    pf_result = run_power_flow("IEEE13", {
        "harmonic_analysis": True,
        "harmonic_orders": [1, 3, 5]
    })

    assert pf_result["success"]
    assert "data" in pf_result
    data = pf_result["data"]

    # Verify harmonics structure is complete
    assert "harmonics" in data
    harmonics = data["harmonics"]

    # Check all required keys exist
    required_keys = ["thd_voltage", "thd_current", "individual_harmonics", "worst_thd_bus", "worst_thd_value"]
    for key in required_keys:
        assert key in harmonics, f"Missing required key: {key}"

    # Verify types
    assert isinstance(harmonics["thd_voltage"], dict)
    assert isinstance(harmonics["thd_current"], dict)
    assert isinstance(harmonics["individual_harmonics"], dict)
    assert isinstance(harmonics["worst_thd_bus"], str)
    assert isinstance(harmonics["worst_thd_value"], (int, float))

    # Verify individual_harmonics has entries for each order
    for order in [1, 3, 5]:
        assert order in harmonics["individual_harmonics"], f"Order {order} missing from individual_harmonics"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
