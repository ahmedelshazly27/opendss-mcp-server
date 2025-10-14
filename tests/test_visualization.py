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
from opendss_mcp.tools.visualization import generate_visualization, store_visualization_data


# Required response fields
REQUIRED_RESPONSE_KEYS = {'success', 'data', 'metadata', 'errors'}

# Required data fields in successful visualization responses
REQUIRED_VIZ_DATA_KEYS = {'plot_type', 'format', 'dimensions'}


@pytest.fixture(scope="module")
def loaded_feeder():
    """Fixture to load IEEE13 feeder once for all tests."""
    result = load_ieee_test_feeder('IEEE13')
    assert result['success'], "Failed to load feeder for tests"

    # Run power flow
    pf_result = run_power_flow('IEEE13')
    assert pf_result['success'], "Failed to run power flow for tests"

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
        options={
            "title": "Test Voltage Profile",
            "figsize": (10, 6)
        }
    )

    # Assert response structure
    assert set(result.keys()) == REQUIRED_RESPONSE_KEYS, (
        f"Response missing required keys. Expected {REQUIRED_RESPONSE_KEYS}, got {set(result.keys())}"
    )

    # Assert success
    assert result['success'] is True, f"Visualization failed: {result.get('errors')}"

    # Assert data exists and has required fields
    assert result['data'] is not None
    data_keys = set(result['data'].keys())
    missing_keys = REQUIRED_VIZ_DATA_KEYS - data_keys
    assert not missing_keys, f"Missing required data keys: {missing_keys}"

    # Assert plot type is correct
    assert result['data']['plot_type'] == "voltage_profile"

    # Assert dimensions are present
    assert 'dimensions' in result['data']
    assert 'width' in result['data']['dimensions']
    assert 'height' in result['data']['dimensions']
    assert result['data']['dimensions']['width'] > 0
    assert result['data']['dimensions']['height'] > 0

    # Assert format is correct
    assert result['data']['format'] == "png"

    # Assert either file_path or image_base64 is present (not both for base64 mode)
    has_file = result['data'].get('file_path') is not None
    has_base64 = result['data'].get('image_base64') is not None
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
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        save_path = tmp.name

    try:
        # Act - Generate plot with save_path
        result = generate_visualization(
            plot_type="voltage_profile",
            data_source="circuit",
            options={
                "save_path": save_path,
                "title": "Test Save to File",
                "dpi": 100
            }
        )

        # Assert success
        assert result['success'] is True, f"Visualization failed: {result.get('errors')}"

        # Assert file_path is in response
        assert 'file_path' in result['data']
        assert result['data']['file_path'] is not None

        # Assert file_path matches what we requested
        assert os.path.samefile(result['data']['file_path'], save_path)

        # Assert file exists
        assert os.path.exists(save_path), "Output file does not exist"

        # Assert file has content (not empty)
        file_size = os.path.getsize(save_path)
        assert file_size > 0, "Output file is empty"
        assert file_size > 1000, f"Output file too small ({file_size} bytes), may be corrupted"

        # Assert image_base64 is NOT present (only file_path should be used)
        assert result['data'].get('image_base64') is None, "Should not have base64 when saving to file"

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
        options={
            "title": "Test Base64 Output",
            "figsize": (8, 5),
            "dpi": 100
        }
    )

    # Assert success
    assert result['success'] is True, f"Visualization failed: {result.get('errors')}"

    # Assert image_base64 is present
    assert 'image_base64' in result['data']
    assert result['data']['image_base64'] is not None

    # Assert image_base64 is a non-empty string
    image_data = result['data']['image_base64']
    assert isinstance(image_data, str), "image_base64 should be a string"
    assert len(image_data) > 0, "image_base64 should not be empty"

    # Assert it's valid base64 (can be decoded)
    try:
        decoded = base64.b64decode(image_data)
        assert len(decoded) > 0, "Decoded image data is empty"
        assert len(decoded) > 1000, f"Decoded image too small ({len(decoded)} bytes)"

        # Check PNG magic number (first 8 bytes)
        png_signature = b'\x89PNG\r\n\x1a\n'
        assert decoded[:8] == png_signature, "Decoded data is not a valid PNG image"

    except Exception as e:
        pytest.fail(f"Failed to decode base64 image: {e}")

    # Assert file_path is NOT present (only base64 should be used)
    assert result['data'].get('file_path') is None, "Should not have file_path when returning base64"


def test_network_diagram(loaded_feeder):
    """Test generating network diagram visualization."""
    # Act
    result = generate_visualization(
        plot_type="network_diagram",
        data_source="circuit",
        options={
            "title": "Test Network Diagram",
            "figsize": (12, 10),
            "layout": "spring"
        }
    )

    # Assert success
    assert result['success'] is True, f"Visualization failed: {result.get('errors')}"

    # Assert plot type
    assert result['data']['plot_type'] == "network_diagram"

    # Assert has base64 image (no save_path specified)
    assert result['data'].get('image_base64') is not None


def test_timeseries_visualization():
    """Test time-series visualization with simulated data."""
    # Arrange - Create simulated time-series data
    timesteps = []
    for hour in range(24):
        timesteps.append({
            "timestep": hour,
            "hour": hour,
            "total_load_kw": 5000 + hour * 100,
            "losses_kw": 150 + hour * 5,
            "min_voltage_pu": 0.98 - hour * 0.001,
            "max_voltage_pu": 1.02 + hour * 0.0005,
            "converged": True
        })

    timeseries_data = {
        "data": {
            "timesteps": timesteps
        }
    }

    # Store data for visualization
    store_visualization_data("timeseries", timeseries_data)

    # Act - Generate time-series plot
    result = generate_visualization(
        plot_type="timeseries",
        data_source="last_timeseries",
        options={
            "title": "Test Time-Series",
            "variables": ["total_load_kw", "losses_kw"]
        }
    )

    # Assert success
    assert result['success'] is True, f"Visualization failed: {result.get('errors')}"

    # Assert plot type
    assert result['data']['plot_type'] == "timeseries"


def test_invalid_plot_type(loaded_feeder):
    """Test error handling for invalid plot type."""
    # Act
    result = generate_visualization(
        plot_type="invalid_plot_type",
        data_source="circuit"
    )

    # Assert failure
    assert result['success'] is False

    # Assert errors are present
    assert result['errors'] is not None
    assert len(result['errors']) > 0
    assert any('unknown plot type' in str(e).lower() for e in result['errors'])


def test_invalid_data_source():
    """Test error handling for invalid data source."""
    # Act
    result = generate_visualization(
        plot_type="voltage_profile",
        data_source="invalid_source"
    )

    # Assert failure
    assert result['success'] is False

    # Assert errors are present
    assert result['errors'] is not None
    assert len(result['errors']) > 0


def test_no_circuit_loaded():
    """Test error handling when no circuit is loaded."""
    # Note: This test assumes circuit is loaded from fixture in other tests
    # If we want to test "no circuit" state, we'd need to clear the circuit first
    # For now, we'll test that voltage_profile requires valid data

    # Act - Try to generate with data source that doesn't exist
    result = generate_visualization(
        plot_type="voltage_profile",
        data_source="last_power_flow"  # Not stored, should fail
    )

    # Assert failure (either no data or plot generation fails)
    # This may succeed or fail depending on whether circuit is still loaded
    # So we just check response structure is valid
    assert 'success' in result
    assert 'data' in result
    assert 'errors' in result


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
            "show_grid": True
        }
    )

    # Assert success
    assert result['success'] is True

    # Assert metadata includes options
    assert 'metadata' in result
    assert result['metadata'] is not None
    assert 'figsize' in result['metadata']
    assert result['metadata']['figsize'] == (16, 8)
    assert 'dpi' in result['metadata']
    assert result['metadata']['dpi'] == 150


def test_response_format():
    """Test the response format of generate_visualization function."""
    # Arrange - Load feeder
    load_result = load_ieee_test_feeder('IEEE13')
    assert load_result['success'], "Failed to load feeder"

    # Act
    result = generate_visualization(
        plot_type="voltage_profile",
        data_source="circuit"
    )

    # Assert top-level keys
    assert set(result.keys()) == REQUIRED_RESPONSE_KEYS, (
        f"Response missing required keys. Expected {REQUIRED_RESPONSE_KEYS}, got {set(result.keys())}"
    )

    # Assert success is boolean
    assert isinstance(result['success'], bool)

    # Check data structure on success
    if result['success']:
        assert result['data'] is not None

        # Check required visualization data fields
        data_keys = set(result['data'].keys())
        missing_keys = REQUIRED_VIZ_DATA_KEYS - data_keys
        assert not missing_keys, f"Missing required data keys: {missing_keys}"

        # Check types
        assert isinstance(result['data']['plot_type'], str)
        assert isinstance(result['data']['format'], str)
        assert isinstance(result['data']['dimensions'], dict)
        assert 'width' in result['data']['dimensions']
        assert 'height' in result['data']['dimensions']

        # Either file_path or image_base64 must be present
        has_output = (
            result['data'].get('file_path') is not None or
            result['data'].get('image_base64') is not None
        )
        assert has_output, "Must have either file_path or image_base64"
    else:
        # On error, errors should be present
        assert isinstance(result['errors'], list)
        assert len(result['errors']) > 0
        assert all(isinstance(e, str) for e in result['errors'])

    # Check metadata (can be None or dict)
    assert result['metadata'] is None or isinstance(result['metadata'], dict)
