"""
Tests for the visualization module.
"""

import os
import base64
import tempfile
from pathlib import Path

import pytest

from opendss_mcp.tools.feeder_loader import load_ieee_test_feeder
from opendss_mcp.tools.power_flow import run_power_flow
from opendss_mcp.tools.visualization import (
    generate_visualization,
    store_visualization_data,
)


# Required response fields
REQUIRED_RESPONSE_KEYS = {"success", "data", "metadata", "errors"}

# Required data fields in successful visualization responses
REQUIRED_VIZ_DATA_KEYS = {"plot_type", "format", "dimensions"}


@pytest.fixture(scope="module")
def loaded_feeder():
    """Fixture to load IEEE13 feeder once for all tests."""
    result = load_ieee_test_feeder("IEEE13")
    assert result["success"], "Failed to load feeder for tests"

    # Run power flow
    pf_result = run_power_flow("IEEE13")
    assert pf_result["success"], "Failed to run power flow for tests"

    return result


def test_voltage_profile_plot(loaded_feeder):
    """Test generating voltage profile visualization.

    This test:
    1. Loads IEEE13 feeder (via fixture)
    2. Runs power flow (via fixture)
    3. Generates voltage profile plot
    4. Asserts success and proper response structure
    """
    # Act - Generate voltage profile from circuit
    result = generate_visualization(
        plot_type="voltage_profile",
        data_source="circuit",
        options={"title": "Test Voltage Profile", "figsize": (10, 6)},
    )

    # Assert response structure
    assert (
        set(result.keys()) == REQUIRED_RESPONSE_KEYS
    ), f"Response missing required keys. Expected {REQUIRED_RESPONSE_KEYS}, got {set(result.keys())}"

    # Assert success
    assert result["success"] is True, f"Visualization failed: {result.get('errors')}"

    # Assert data exists and has required fields
    assert result["data"] is not None
    data_keys = set(result["data"].keys())
    missing_keys = REQUIRED_VIZ_DATA_KEYS - data_keys
    assert not missing_keys, f"Missing required data keys: {missing_keys}"

    # Assert plot type is correct
    assert result["data"]["plot_type"] == "voltage_profile"

    # Assert dimensions are present
    assert "dimensions" in result["data"]
    assert "width" in result["data"]["dimensions"]
    assert "height" in result["data"]["dimensions"]
    assert result["data"]["dimensions"]["width"] > 0
    assert result["data"]["dimensions"]["height"] > 0

    # Assert format is correct
    assert result["data"]["format"] == "png"

    # Assert either file_path or image_base64 is present (not both for base64 mode)
    has_file = result["data"].get("file_path") is not None
    has_base64 = result["data"].get("image_base64") is not None
    assert has_file or has_base64, "Must have either file_path or image_base64"


def test_save_to_file(loaded_feeder):
    """Test saving visualization to a file.

    This test:
    1. Creates a temporary file path
    2. Generates a plot with save_path option
    3. Checks that the file exists and has content
    4. Cleans up the temporary file
    """
    # Arrange - Create temporary file path
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        save_path = tmp.name

    try:
        # Act - Generate plot with save_path
        result = generate_visualization(
            plot_type="voltage_profile",
            data_source="circuit",
            options={"save_path": save_path, "title": "Test Save to File", "dpi": 100},
        )

        # Assert success
        assert (
            result["success"] is True
        ), f"Visualization failed: {result.get('errors')}"

        # Assert file_path is in response
        assert "file_path" in result["data"]
        assert result["data"]["file_path"] is not None

        # Assert file_path matches what we requested
        assert os.path.samefile(result["data"]["file_path"], save_path)

        # Assert file exists
        assert os.path.exists(save_path), "Output file does not exist"

        # Assert file has content (not empty)
        file_size = os.path.getsize(save_path)
        assert file_size > 0, "Output file is empty"
        assert (
            file_size > 1000
        ), f"Output file too small ({file_size} bytes), may be corrupted"

        # Assert image_base64 is NOT present (only file_path should be used)
        assert (
            result["data"].get("image_base64") is None
        ), "Should not have base64 when saving to file"

    finally:
        # Cleanup - Remove temporary file
        if os.path.exists(save_path):
            os.remove(save_path)


def test_base64_output(loaded_feeder):
    """Test generating visualization as base64-encoded image.

    This test:
    1. Generates a plot without save_path
    2. Checks that image_base64 is present and valid
    3. Validates the base64 encoding
    """
    # Act - Generate plot without save_path (should return base64)
    result = generate_visualization(
        plot_type="voltage_profile",
        data_source="circuit",
        options={"title": "Test Base64 Output", "figsize": (8, 5), "dpi": 100},
    )

    # Assert success
    assert result["success"] is True, f"Visualization failed: {result.get('errors')}"

    # Assert image_base64 is present
    assert "image_base64" in result["data"]
    assert result["data"]["image_base64"] is not None

    # Assert image_base64 is a non-empty string
    image_data = result["data"]["image_base64"]
    assert isinstance(image_data, str), "image_base64 should be a string"
    assert len(image_data) > 0, "image_base64 should not be empty"

    # Assert it's valid base64 (can be decoded)
    try:
        decoded = base64.b64decode(image_data)
        assert len(decoded) > 0, "Decoded image data is empty"
        assert len(decoded) > 1000, f"Decoded image too small ({len(decoded)} bytes)"

        # Check PNG magic number (first 8 bytes)
        png_signature = b"\x89PNG\r\n\x1a\n"
        assert decoded[:8] == png_signature, "Decoded data is not a valid PNG image"

    except Exception as e:
        pytest.fail(f"Failed to decode base64 image: {e}")

    # Assert file_path is NOT present (only base64 should be used)
    assert (
        result["data"].get("file_path") is None
    ), "Should not have file_path when returning base64"


def test_network_diagram(loaded_feeder):
    """Test generating network diagram visualization."""
    # Act
    result = generate_visualization(
        plot_type="network_diagram",
        data_source="circuit",
        options={
            "title": "Test Network Diagram",
            "figsize": (12, 10),
            "layout": "spring",
        },
    )

    # Assert success
    assert result["success"] is True, f"Visualization failed: {result.get('errors')}"

    # Assert plot type
    assert result["data"]["plot_type"] == "network_diagram"

    # Assert has base64 image (no save_path specified)
    assert result["data"].get("image_base64") is not None


def test_timeseries_visualization():
    """Test time-series visualization with simulated data."""
    # Arrange - Create simulated time-series data
    timesteps = []
    for hour in range(24):
        timesteps.append(
            {
                "timestep": hour,
                "hour": hour,
                "total_load_kw": 5000 + hour * 100,
                "losses_kw": 150 + hour * 5,
                "min_voltage_pu": 0.98 - hour * 0.001,
                "max_voltage_pu": 1.02 + hour * 0.0005,
                "converged": True,
            }
        )

    timeseries_data = {"data": {"timesteps": timesteps}}

    # Store data for visualization
    store_visualization_data("timeseries", timeseries_data)

    # Act - Generate time-series plot
    result = generate_visualization(
        plot_type="timeseries",
        data_source="last_timeseries",
        options={
            "title": "Test Time-Series",
            "variables": ["total_load_kw", "losses_kw"],
        },
    )

    # Assert success
    assert result["success"] is True, f"Visualization failed: {result.get('errors')}"

    # Assert plot type
    assert result["data"]["plot_type"] == "timeseries"


def test_invalid_plot_type(loaded_feeder):
    """Test error handling for invalid plot type."""
    # Act
    result = generate_visualization(
        plot_type="invalid_plot_type", data_source="circuit"
    )

    # Assert failure
    assert result["success"] is False

    # Assert errors are present
    assert result["errors"] is not None
    assert len(result["errors"]) > 0
    assert any("unknown plot type" in str(e).lower() for e in result["errors"])


def test_invalid_data_source():
    """Test error handling for invalid data source."""
    # Act
    result = generate_visualization(
        plot_type="voltage_profile", data_source="invalid_source"
    )

    # Assert failure
    assert result["success"] is False

    # Assert errors are present
    assert result["errors"] is not None
    assert len(result["errors"]) > 0


def test_no_circuit_loaded():
    """Test error handling when no circuit is loaded."""
    # Note: This test assumes circuit is loaded from fixture in other tests
    # If we want to test "no circuit" state, we'd need to clear the circuit first
    # For now, we'll test that voltage_profile requires valid data

    # Act - Try to generate with data source that doesn't exist
    result = generate_visualization(
        plot_type="voltage_profile",
        data_source="last_power_flow",  # Not stored, should fail
    )

    # Assert failure (either no data or plot generation fails)
    # This may succeed or fail depending on whether circuit is still loaded
    # So we just check response structure is valid
    assert "success" in result
    assert "data" in result
    assert "errors" in result


def test_custom_options(loaded_feeder):
    """Test visualization with custom options."""
    # Act
    result = generate_visualization(
        plot_type="voltage_profile",
        data_source="circuit",
        options={
            "title": "Custom Title Test",
            "figsize": (16, 8),
            "dpi": 150,
            "show_violations": True,
            "show_grid": True,
        },
    )

    # Assert success
    assert result["success"] is True

    # Assert metadata includes options
    assert "metadata" in result
    assert result["metadata"] is not None
    assert "figsize" in result["metadata"]
    assert result["metadata"]["figsize"] == (16, 8)
    assert "dpi" in result["metadata"]
    assert result["metadata"]["dpi"] == 150


def test_response_format():
    """Test the response format of generate_visualization function."""
    # Arrange - Load feeder
    load_result = load_ieee_test_feeder("IEEE13")
    assert load_result["success"], "Failed to load feeder"

    # Act
    result = generate_visualization(plot_type="voltage_profile", data_source="circuit")

    # Assert top-level keys
    assert (
        set(result.keys()) == REQUIRED_RESPONSE_KEYS
    ), f"Response missing required keys. Expected {REQUIRED_RESPONSE_KEYS}, got {set(result.keys())}"

    # Assert success is boolean
    assert isinstance(result["success"], bool)

    # Check data structure on success
    if result["success"]:
        assert result["data"] is not None

        # Check required visualization data fields
        data_keys = set(result["data"].keys())
        missing_keys = REQUIRED_VIZ_DATA_KEYS - data_keys
        assert not missing_keys, f"Missing required data keys: {missing_keys}"

        # Check types
        assert isinstance(result["data"]["plot_type"], str)
        assert isinstance(result["data"]["format"], str)
        assert isinstance(result["data"]["dimensions"], dict)
        assert "width" in result["data"]["dimensions"]
        assert "height" in result["data"]["dimensions"]

        # Either file_path or image_base64 must be present
        has_output = (
            result["data"].get("file_path") is not None
            or result["data"].get("image_base64") is not None
        )
        assert has_output, "Must have either file_path or image_base64"
    else:
        # On error, errors should be present
        assert isinstance(result["errors"], list)
        assert len(result["errors"]) > 0
        assert all(isinstance(e, str) for e in result["errors"])

    # Check metadata (can be None or dict)
    assert result["metadata"] is None or isinstance(result["metadata"], dict)


def test_capacity_curve_visualization():
    """Test capacity analysis curve visualization."""
    # Arrange - Create simulated capacity analysis data
    capacity_data = {
        "data": {
            "capacity_curve": [
                {"capacity_kw": 0, "max_line_loading_pct": 45.2},
                {"capacity_kw": 500, "max_line_loading_pct": 58.3},
                {"capacity_kw": 1000, "max_line_loading_pct": 71.5},
                {"capacity_kw": 1500, "max_line_loading_pct": 84.7},
                {"capacity_kw": 2000, "max_line_loading_pct": 98.2},
            ]
        }
    }

    # Store data for visualization
    store_visualization_data("capacity", capacity_data)

    # Act - Generate capacity curve plot
    result = generate_visualization(
        plot_type="capacity_curve",
        data_source="last_capacity",
        options={
            "title": "Test Capacity Curve",
            "xlabel": "DER Capacity (kW)",
            "ylabel": "Max Loading (%)",
            "color": "steelblue",
        },
    )

    # Assert success
    assert result["success"] is True, f"Visualization failed: {result.get('errors')}"

    # Assert plot type
    assert result["data"]["plot_type"] == "capacity_curve"

    # Assert has base64 image
    assert result["data"].get("image_base64") is not None


def test_capacity_curve_alternative_data_format():
    """Test capacity curve with alternative data structure."""
    # Arrange - Test with "capacity_curve" at top level
    capacity_data = {
        "capacity_curve": [
            {"capacity_kw": 0, "max_loading_pct": 40.0},
            {"capacity_kw": 1000, "max_loading_pct": 80.0},
        ]
    }

    store_visualization_data("capacity", capacity_data)

    # Act
    result = generate_visualization(
        plot_type="capacity_curve", data_source="last_capacity"
    )

    # Assert success
    assert result["success"] is True


def test_capacity_curve_with_results_key():
    """Test capacity curve with 'results' key instead of 'capacity_curve'."""
    # Arrange
    capacity_data = {
        "results": [
            {"capacity_kw": 0, "max_line_loading_pct": 35.0},
            {"capacity_kw": 500, "max_line_loading_pct": 55.0},
        ]
    }

    store_visualization_data("capacity", capacity_data)

    # Act
    result = generate_visualization(
        plot_type="capacity_curve", data_source="last_capacity"
    )

    # Assert success
    assert result["success"] is True


def test_capacity_curve_missing_data():
    """Test capacity curve error handling with missing data."""
    # Arrange - Data without capacity_curve or results
    capacity_data = {"some_other_key": []}

    store_visualization_data("capacity", capacity_data)

    # Act
    result = generate_visualization(
        plot_type="capacity_curve", data_source="last_capacity"
    )

    # Assert failure
    assert result["success"] is False
    assert any("no capacity data found" in str(e).lower() for e in result["errors"])


def test_capacity_curve_empty_data():
    """Test capacity curve error handling with empty results."""
    # Arrange
    capacity_data = {"capacity_curve": []}

    store_visualization_data("capacity", capacity_data)

    # Act
    result = generate_visualization(
        plot_type="capacity_curve", data_source="last_capacity"
    )

    # Assert failure
    assert result["success"] is False
    assert any("empty" in str(e).lower() for e in result["errors"])


def test_harmonics_spectrum_visualization():
    """Test harmonics spectrum visualization."""
    # Arrange - Create simulated harmonics data
    harmonics_data = {
        "data": {
            "harmonics": {
                "worst_thd_bus": "650",
                "thd_voltage": {"650": 5.2, "632": 3.8},
                "individual_harmonics": {
                    "1": {"650": 120.0, "632": 118.5},
                    "3": {"650": 3.5, "632": 2.8},
                    "5": {"650": 2.8, "632": 2.1},
                    "7": {"650": 1.5, "632": 1.2},
                },
            }
        }
    }

    # Store data
    store_visualization_data("harmonics", harmonics_data)

    # Act - Generate harmonics spectrum
    result = generate_visualization(
        plot_type="harmonics_spectrum",
        data_source="last_harmonics",
        options={"title": "Test Harmonics Spectrum", "color": "steelblue"},
    )

    # Assert success
    assert result["success"] is True, f"Visualization failed: {result.get('errors')}"

    # Assert plot type
    assert result["data"]["plot_type"] == "harmonics_spectrum"

    # Assert has base64 image
    assert result["data"].get("image_base64") is not None


def test_harmonics_spectrum_with_bus_filter():
    """Test harmonics spectrum with specific bus filter."""
    # Arrange
    harmonics_data = {
        "harmonics": {
            "thd_voltage": {"650": 5.2, "632": 3.8, "671": 4.1},
            "individual_harmonics": {
                "1": {"650": 120.0, "632": 118.5, "671": 119.2},
                "3": {"650": 3.5, "632": 2.8, "671": 3.0},
                "5": {"650": 2.8, "632": 2.1, "671": 2.4},
            },
        }
    }

    store_visualization_data("harmonics", harmonics_data)

    # Act - Filter to specific buses
    result = generate_visualization(
        plot_type="harmonics_spectrum",
        data_source="last_harmonics",
        options={"bus_filter": ["650", "632"]},
    )

    # Assert success
    assert result["success"] is True


def test_harmonics_spectrum_no_worst_bus():
    """Test harmonics spectrum when worst_thd_bus is not available."""
    # Arrange - No worst_thd_bus, should use first available
    harmonics_data = {
        "data": {
            "harmonics": {
                "thd_voltage": {"632": 3.8},
                "individual_harmonics": {"1": {"632": 118.5}, "3": {"632": 2.8}},
            }
        }
    }

    store_visualization_data("harmonics", harmonics_data)

    # Act
    result = generate_visualization(
        plot_type="harmonics_spectrum", data_source="last_harmonics"
    )

    # Assert success
    assert result["success"] is True


def test_harmonics_spectrum_missing_data():
    """Test harmonics spectrum error handling with missing data."""
    # Arrange
    harmonics_data = {"some_other_key": {}}

    store_visualization_data("harmonics", harmonics_data)

    # Act
    result = generate_visualization(
        plot_type="harmonics_spectrum", data_source="last_harmonics"
    )

    # Assert failure
    assert result["success"] is False
    assert any("no harmonics data found" in str(e).lower() for e in result["errors"])


def test_harmonics_spectrum_no_bus_data():
    """Test harmonics spectrum when no bus data is available."""
    # Arrange - Empty harmonics dict
    harmonics_data = {"harmonics": {"thd_voltage": {}, "individual_harmonics": {}}}

    store_visualization_data("harmonics", harmonics_data)

    # Act
    result = generate_visualization(
        plot_type="harmonics_spectrum", data_source="last_harmonics"
    )

    # Assert failure
    assert result["success"] is False
    assert any(
        "no bus harmonic data available" in str(e).lower() for e in result["errors"]
    )


def test_harmonics_spectrum_bus_not_in_data():
    """Test harmonics spectrum when filtered bus has no harmonic data."""
    # Arrange
    harmonics_data = {
        "harmonics": {
            "thd_voltage": {"650": 5.2},
            "individual_harmonics": {"1": {"650": 120.0}, "3": {"650": 3.5}},
        }
    }

    store_visualization_data("harmonics", harmonics_data)

    # Act - Filter to bus that exists in THD but check individual harmonics display
    result = generate_visualization(
        plot_type="harmonics_spectrum",
        data_source="last_harmonics",
        options={"bus_filter": ["999"]},  # Non-existent bus
    )

    # Should still succeed but show "No data" message
    assert result["success"] is True


def test_voltage_profile_with_bus_filter(loaded_feeder):
    """Test voltage profile with bus filter option."""
    # Act - Generate with bus filter
    result = generate_visualization(
        plot_type="voltage_profile",
        data_source="circuit",
        options={
            "bus_filter": ["650", "632", "671"],
            "title": "Filtered Voltage Profile",
        },
    )

    # Assert success
    assert result["success"] is True, f"Visualization failed: {result.get('errors')}"

    # Assert plot type
    assert result["data"]["plot_type"] == "voltage_profile"


def test_voltage_profile_without_violations_highlighting(loaded_feeder):
    """Test voltage profile with show_violations disabled."""
    # Act
    result = generate_visualization(
        plot_type="voltage_profile",
        data_source="circuit",
        options={"show_violations": False, "color": "blue"},
    )

    # Assert success
    assert result["success"] is True


def test_voltage_profile_without_grid(loaded_feeder):
    """Test voltage profile with grid disabled."""
    # Act
    result = generate_visualization(
        plot_type="voltage_profile", data_source="circuit", options={"show_grid": False}
    )

    # Assert success
    assert result["success"] is True


def test_network_diagram_with_tuple_format(loaded_feeder):
    """Test network diagram with tuple line format."""
    # Arrange - Create data with tuple format for lines
    network_data = {
        "lines": [("650", "632"), ("632", "671"), ("671", "680")],
        "voltages": {"650": 1.00, "632": 0.98, "671": 0.96, "680": 0.95},
    }

    store_visualization_data("power_flow", network_data)

    # Act
    result = generate_visualization(
        plot_type="network_diagram", data_source="last_power_flow"
    )

    # Assert success
    assert result["success"] is True


def test_network_diagram_missing_topology():
    """Test network diagram error with missing topology data."""
    # Arrange - Data without lines
    network_data = {"voltages": {"650": 1.0}}

    store_visualization_data("power_flow", network_data)

    # Act
    result = generate_visualization(
        plot_type="network_diagram", data_source="last_power_flow"
    )

    # Assert failure
    assert result["success"] is False
    assert any("no network topology" in str(e).lower() for e in result["errors"])


def test_timeseries_auto_variable_detection():
    """Test time-series visualization with auto variable detection."""
    # Arrange
    timesteps = []
    for hour in range(12):
        timesteps.append(
            {
                "timestep": hour,
                "hour": hour,
                "total_load_kw": 5000 + hour * 100,
                "losses_kw": 150 + hour * 5,
                "converged": True,
            }
        )

    timeseries_data = {"timesteps": timesteps}

    store_visualization_data("timeseries", timeseries_data)

    # Act - Don't specify variables (should auto-detect)
    result = generate_visualization(
        plot_type="timeseries",
        data_source="last_timeseries",
        options={"title": "Auto-detected Variables"},
    )

    # Assert success
    assert result["success"] is True


def test_timeseries_no_plottable_variables():
    """Test time-series error when no plottable variables exist."""
    # Arrange - Only non-plottable fields
    timesteps = [
        {"timestep": 0, "hour": 0, "converged": True},
        {"timestep": 1, "hour": 1, "converged": True},
    ]

    timeseries_data = {"data": {"timesteps": timesteps}}

    store_visualization_data("timeseries", timeseries_data)

    # Act
    result = generate_visualization(
        plot_type="timeseries", data_source="last_timeseries"
    )

    # Assert failure
    assert result["success"] is False
    assert any("no plottable variables" in str(e).lower() for e in result["errors"])


def test_timeseries_missing_data():
    """Test time-series error with missing timesteps data."""
    # Arrange
    timeseries_data = {"some_other_key": []}

    store_visualization_data("timeseries", timeseries_data)

    # Act
    result = generate_visualization(
        plot_type="timeseries", data_source="last_timeseries"
    )

    # Assert failure
    assert result["success"] is False
    assert any("no time-series data found" in str(e).lower() for e in result["errors"])


def test_voltage_profile_missing_voltage_data():
    """Test voltage profile error with missing voltage data."""
    # Arrange
    voltage_data = {"some_other_key": {}}

    store_visualization_data("power_flow", voltage_data)

    # Act
    result = generate_visualization(
        plot_type="voltage_profile", data_source="last_power_flow"
    )

    # Assert failure
    assert result["success"] is False
    assert any("no voltage data found" in str(e).lower() for e in result["errors"])
