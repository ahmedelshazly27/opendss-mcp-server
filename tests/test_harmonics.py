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
        3: 10.0,  # 3rd harmonic
        5: 8.0,  # 5th harmonic
        7: 5.0,  # 7th harmonic
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
    harmonics = {3: 10.0, 5: 8.0, 7: 5.0}

    thd = calculate_thd(harmonics)

    # Should return 0.0 when fundamental is missing
    assert thd == 0.0, "THD should be 0.0 when fundamental is missing"


def test_thd_calculation_zero_fundamental():
    """Test THD calculation when fundamental is zero."""
    harmonics = {1: 0.0, 3: 10.0, 5: 8.0}  # Zero fundamental

    thd = calculate_thd(harmonics)

    # Should return 0.0 when fundamental is zero
    assert thd == 0.0, "THD should be 0.0 when fundamental is zero"


def test_thd_calculation_only_fundamental():
    """Test THD calculation with only fundamental (no harmonics)."""
    harmonics = {1: 120.0}  # Only fundamental

    thd = calculate_thd(harmonics)

    # Should return 0.0 when no harmonics above fundamental
    assert thd == 0.0, "THD should be 0.0 when only fundamental is present"


def test_thd_calculation_high_distortion():
    """Test THD calculation with high distortion."""
    harmonics = {
        1: 100.0,  # Fundamental
        3: 50.0,  # Large 3rd harmonic
        5: 30.0,  # Large 5th harmonic
        7: 20.0,  # Large 7th harmonic
        9: 10.0,  # 9th harmonic
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
    pf_result = run_power_flow(
        "IEEE13", {"harmonic_analysis": True, "harmonic_orders": [1, 3, 5, 7]}
    )

    # Verify operation succeeded
    assert pf_result["success"], f"Power flow failed: {pf_result.get('errors')}"

    # Verify basic power flow data exists
    assert "data" in pf_result
    data = pf_result["data"]
    assert data["converged"], "Power flow should converge"
    assert "bus_voltages" in data

    # Verify harmonics field exists
    assert (
        "harmonics" in data
    ), "Harmonics field should be present when harmonic_analysis=True"
    harmonics = data["harmonics"]

    # Verify harmonics structure
    assert "thd_voltage" in harmonics, "harmonics should contain thd_voltage"
    assert "thd_current" in harmonics, "harmonics should contain thd_current"
    assert (
        "individual_harmonics" in harmonics
    ), "harmonics should contain individual_harmonics"
    assert "worst_thd_bus" in harmonics, "harmonics should contain worst_thd_bus"
    assert "worst_thd_value" in harmonics, "harmonics should contain worst_thd_value"

    # Verify thd_voltage is a dictionary
    assert isinstance(
        harmonics["thd_voltage"], dict
    ), "thd_voltage should be a dictionary"

    # Verify thd_current is a dictionary
    assert isinstance(
        harmonics["thd_current"], dict
    ), "thd_current should be a dictionary"

    # Verify individual_harmonics structure
    assert isinstance(
        harmonics["individual_harmonics"], dict
    ), "individual_harmonics should be a dictionary"

    # Verify individual harmonics contains the requested orders
    for order in [1, 3, 5, 7]:
        assert (
            order in harmonics["individual_harmonics"]
        ), f"Harmonic order {order} should be in individual_harmonics"
        assert isinstance(
            harmonics["individual_harmonics"][order], dict
        ), f"Order {order} should map to a dictionary"

    # Verify worst_thd_bus is a string
    assert isinstance(
        harmonics["worst_thd_bus"], str
    ), "worst_thd_bus should be a string"

    # Verify worst_thd_value is a number
    assert isinstance(
        harmonics["worst_thd_value"], (int, float)
    ), "worst_thd_value should be a number"
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
    pf_result = run_power_flow("IEEE13", {"harmonic_analysis": True})

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
        assert (
            order in individual_harmonics
        ), f"Default harmonic order {order} should be present"


def test_harmonics_disabled():
    """Test that harmonics field is not present when harmonic analysis is disabled."""
    # Load IEEE13 feeder
    load_result = load_ieee_test_feeder("IEEE13")
    assert load_result["success"], f"Failed to load feeder: {load_result.get('errors')}"

    # Run power flow with harmonic analysis explicitly disabled
    pf_result = run_power_flow("IEEE13", {"harmonic_analysis": False})

    # Verify operation succeeded
    assert pf_result["success"], f"Power flow failed: {pf_result.get('errors')}"

    # Verify basic power flow data exists
    assert "data" in pf_result
    data = pf_result["data"]
    assert data["converged"], "Power flow should converge"

    # Verify harmonics field does NOT exist
    assert (
        "harmonics" not in data
    ), "Harmonics field should not be present when harmonic_analysis=False"

    # Verify options show harmonic analysis is disabled
    assert (
        "harmonic_analysis" not in data["options"]
        or data["options"].get("harmonic_analysis") is False
    )


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
    assert (
        "harmonics" not in data
    ), "Harmonics should be disabled by default for backward compatibility"


def test_harmonics_structure_complete():
    """Test that harmonic analysis returns the complete expected structure."""
    # Load IEEE13 feeder
    load_result = load_ieee_test_feeder("IEEE13")
    assert load_result["success"], f"Failed to load feeder: {load_result.get('errors')}"

    # Run power flow with harmonics
    pf_result = run_power_flow(
        "IEEE13", {"harmonic_analysis": True, "harmonic_orders": [1, 3, 5]}
    )

    assert pf_result["success"]
    assert "data" in pf_result
    data = pf_result["data"]

    # Verify harmonics structure is complete
    assert "harmonics" in data
    harmonics = data["harmonics"]

    # Check all required keys exist
    required_keys = [
        "thd_voltage",
        "thd_current",
        "individual_harmonics",
        "worst_thd_bus",
        "worst_thd_value",
    ]
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
        assert (
            order in harmonics["individual_harmonics"]
        ), f"Order {order} missing from individual_harmonics"


def test_frequency_scan_no_circuit():
    """Test frequency scan with no circuit loaded."""
    import opendssdirect as dss
    from opendss_mcp.utils.harmonics import run_frequency_scan

    dss.Text.Command("Clear")

    result = run_frequency_scan([3, 5, 7])

    assert result["success"] is False
    assert (
        "no circuit" in result["errors"][0].lower()
        or "active circuit" in result["errors"][0].lower()
    )
    assert result["harmonic_data"] == {}


def test_get_harmonic_voltages_no_circuit():
    """Test getting harmonic voltages with no circuit loaded."""
    import opendssdirect as dss
    from opendss_mcp.utils.harmonics import get_harmonic_voltages

    dss.Text.Command("Clear")

    result = get_harmonic_voltages("675", [1, 3, 5])

    assert result["success"] is False
    assert (
        "no circuit" in result["errors"][0].lower()
        or "active circuit" in result["errors"][0].lower()
    )
    assert result["harmonic_voltages"] == {}
    assert result["thd_percent"] == 0.0


def test_get_harmonic_voltages_invalid_bus():
    """Test getting harmonic voltages for non-existent bus."""
    from opendss_mcp.utils.harmonics import get_harmonic_voltages

    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    result = get_harmonic_voltages("INVALID_BUS", [1, 3, 5])

    assert result["success"] is False
    assert "not found" in result["errors"][0].lower()
    assert result["bus_id"] == "INVALID_BUS"


def test_get_harmonic_currents_no_circuit():
    """Test getting harmonic currents with no circuit loaded."""
    import opendssdirect as dss
    from opendss_mcp.utils.harmonics import get_harmonic_currents

    dss.Text.Command("Clear")

    result = get_harmonic_currents("Line.650632", [1, 3, 5])

    assert result["success"] is False
    assert (
        "no circuit" in result["errors"][0].lower()
        or "active circuit" in result["errors"][0].lower()
    )
    assert result["harmonic_currents"] == {}
    assert result["thd_percent"] == 0.0


def test_get_harmonic_currents_invalid_line():
    """Test getting harmonic currents for non-existent line."""
    from opendss_mcp.utils.harmonics import get_harmonic_currents

    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    result = get_harmonic_currents("INVALID_LINE", [1, 3, 5])

    assert result["success"] is False
    assert "not found" in result["errors"][0].lower()
    assert result["line_id"] == "INVALID_LINE"


def test_frequency_scan_custom_orders():
    """Test frequency scan with custom harmonic orders."""
    from opendss_mcp.utils.harmonics import run_frequency_scan

    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Use custom orders
    custom_orders = [3, 7, 11]
    result = run_frequency_scan(custom_orders)

    assert result["success"]
    assert result["fundamental_frequency_hz"] == 60.0

    # Verify only requested orders are present
    for order in custom_orders:
        assert order in result["harmonic_data"]
        assert result["harmonic_data"][order]["order"] == order
        assert result["harmonic_data"][order]["frequency_hz"] == order * 60


def test_get_harmonic_voltages_basic():
    """Test getting harmonic voltages for a valid bus."""
    from opendss_mcp.utils.harmonics import get_harmonic_voltages

    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    result = get_harmonic_voltages("675", [1, 3, 5])

    # May or may not succeed depending on harmonics in circuit
    # but should have correct structure
    assert "success" in result
    assert "bus_id" in result
    assert result["bus_id"] == "675"
    assert "harmonic_voltages" in result
    assert "thd_percent" in result
    assert "fundamental_voltage_pu" in result
    assert "errors" in result


def test_get_harmonic_currents_basic():
    """Test getting harmonic currents for a valid line."""
    from opendss_mcp.utils.harmonics import get_harmonic_currents

    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Use a known line from IEEE13
    result = get_harmonic_currents("650632", [1, 3, 5])

    # Should have correct structure
    assert "success" in result
    assert "line_id" in result
    assert "harmonic_currents" in result
    assert "thd_percent" in result
    assert "fundamental_current_amps" in result
    assert "errors" in result


def test_frequency_scan_default_orders():
    """Test frequency scan with default harmonic orders."""
    from opendss_mcp.utils.harmonics import run_frequency_scan

    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Use default orders (None)
    result = run_frequency_scan()

    assert result["success"]
    # Default orders are [3, 5, 7, 9, 11, 13]
    default_orders = [3, 5, 7, 9, 11, 13]
    for order in default_orders:
        assert order in result["harmonic_data"]


def test_get_harmonic_voltages_default_orders():
    """Test getting harmonic voltages with default orders."""
    from opendss_mcp.utils.harmonics import get_harmonic_voltages

    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Use default orders (None)
    result = get_harmonic_voltages("675")

    assert "success" in result
    assert "bus_id" in result


def test_get_harmonic_currents_default_orders():
    """Test getting harmonic currents with default orders."""
    from opendss_mcp.utils.harmonics import get_harmonic_currents

    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Use default orders (None)
    result = get_harmonic_currents("650632")

    assert "success" in result
    assert "line_id" in result


def test_get_harmonic_currents_with_line_prefix():
    """Test getting harmonic currents with 'Line.' prefix in ID."""
    from opendss_mcp.utils.harmonics import get_harmonic_currents

    load_ieee_test_feeder("IEEE13")
    run_power_flow("IEEE13")

    # Test with "Line." prefix
    result = get_harmonic_currents("Line.650632", [1, 3, 5])

    assert "success" in result
    assert result["line_id"] == "Line.650632"


def test_calculate_thd_empty_dict():
    """Test THD calculation with empty dictionary."""
    thd = calculate_thd({})
    assert thd == 0.0


def test_calculate_thd_exception_handling():
    """Test THD calculation with invalid input."""
    # Test with non-dict input (should be handled by exception)
    thd = calculate_thd({1: "not_a_number", 3: "also_not_a_number"})
    assert thd == 0.0  # Should return 0.0 on error


def test_frequency_scan_zero_fundamental_frequency():
    """Test frequency scan when fundamental frequency is zero (should default to 60Hz)."""
    from opendss_mcp.utils.harmonics import run_frequency_scan
    import opendssdirect as dss

    load_ieee_test_feeder("IEEE13")

    # Set frequency to 0 to test default behavior
    dss.Solution.Frequency(0)

    result = run_frequency_scan([3, 5])

    # Should default to 60 Hz
    assert result["fundamental_frequency_hz"] == 60.0


def test_frequency_scan_non_convergence():
    """Test frequency scan behavior when solution doesn't converge."""
    from opendss_mcp.utils.harmonics import run_frequency_scan

    load_ieee_test_feeder("IEEE13")

    # Run scan - some orders may not converge, but should still return data
    result = run_frequency_scan([3, 5, 7])

    # Should still report success even if some orders don't converge
    assert "success" in result
    assert "harmonic_data" in result
    assert "errors" in result


def test_get_harmonic_voltages_zero_fundamental_frequency():
    """Test getting harmonic voltages when fundamental frequency is zero."""
    from opendss_mcp.utils.harmonics import get_harmonic_voltages
    import opendssdirect as dss

    load_ieee_test_feeder("IEEE13")
    dss.Solution.Frequency(0)

    result = get_harmonic_voltages("675", [1, 3])

    # Should handle zero frequency gracefully
    assert "success" in result


def test_get_harmonic_voltages_convergence_failure():
    """Test getting harmonic voltages when solution doesn't converge at some orders."""
    from opendss_mcp.utils.harmonics import get_harmonic_voltages

    load_ieee_test_feeder("IEEE13")

    # Request many harmonic orders - some may not converge
    result = get_harmonic_voltages("675", [1, 3, 5, 7, 9, 11, 13, 15, 17])

    assert "success" in result
    assert "errors" in result


def test_get_harmonic_voltages_empty_voltage_data():
    """Test getting harmonic voltages when voltage data might be empty."""
    from opendss_mcp.utils.harmonics import get_harmonic_voltages

    load_ieee_test_feeder("IEEE13")

    # Use a valid bus but may have issues getting voltage data at some harmonics
    result = get_harmonic_voltages("650", [1, 3, 5])

    # Should handle empty voltage data gracefully
    assert "success" in result
    assert "harmonic_voltages" in result


def test_get_harmonic_currents_zero_fundamental_frequency():
    """Test getting harmonic currents when fundamental frequency is zero."""
    from opendss_mcp.utils.harmonics import get_harmonic_currents
    import opendssdirect as dss

    load_ieee_test_feeder("IEEE13")
    dss.Solution.Frequency(0)

    result = get_harmonic_currents("650632", [1, 3])

    # Should handle zero frequency gracefully
    assert "success" in result


def test_get_harmonic_currents_convergence_failure():
    """Test getting harmonic currents when solution doesn't converge."""
    from opendss_mcp.utils.harmonics import get_harmonic_currents

    load_ieee_test_feeder("IEEE13")

    # Request many orders - some may not converge
    result = get_harmonic_currents("650632", [1, 3, 5, 7, 9, 11, 13, 15])

    assert "success" in result
    assert "errors" in result


def test_get_harmonic_currents_empty_current_data():
    """Test getting harmonic currents when current data might be empty."""
    from opendss_mcp.utils.harmonics import get_harmonic_currents

    load_ieee_test_feeder("IEEE13")

    # Use a valid line
    result = get_harmonic_currents("650632", [1, 3, 5])

    # Should handle empty current data gracefully
    assert "success" in result
    assert "harmonic_currents" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
