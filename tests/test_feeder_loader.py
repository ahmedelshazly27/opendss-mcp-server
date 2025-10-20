"""
Tests for the feeder_loader module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from opendss_mcp.tools.feeder_loader import load_ieee_test_feeder

# Required response fields
REQUIRED_RESPONSE_KEYS = {"success", "data", "metadata", "errors"}
# Required data fields in successful responses
REQUIRED_DATA_KEYS = {
    "feeder_id",
    "num_buses",
    "num_lines",
    "num_loads",
    "num_transformers",
    "total_load_kw",
    "total_load_kvar",
    "voltage_bases_kv",
    "feeder_length_km",
}


def test_load_ieee13():
    """Test loading the IEEE13 test feeder."""
    # Act
    result = load_ieee_test_feeder("IEEE13")

    # Assert response structure
    assert "success" in result
    assert result["success"] is True

    # Assert data exists and has required fields
    assert "data" in result
    assert result["data"] is not None

    # Check bus count
    assert result["data"]["num_buses"] == 16  # Updated to match actual feeder

    # Verify feeder_id matches
    assert result["data"]["feeder_id"] == "IEEE13"


def test_load_ieee34():
    """Test loading the IEEE34 test feeder."""
    # Act
    result = load_ieee_test_feeder("IEEE34")

    # Assert response structure
    assert "success" in result
    assert result["success"] is True

    # Assert data exists and has required fields
    assert "data" in result
    assert result["data"] is not None

    # Check bus count
    assert result["data"]["num_buses"] == 37  # Updated to match actual feeder

    # Verify feeder_id matches
    assert result["data"]["feeder_id"] == "IEEE34"


def test_load_ieee123():
    """Test loading the IEEE123 test feeder."""
    # Act
    result = load_ieee_test_feeder("IEEE123")

    # Assert response structure
    assert "success" in result
    # Note: Success expected but loads file missing (see test_feeders.py for expected 0 loads)
    assert result["success"] is True

    # Assert data exists and has required fields
    assert "data" in result
    assert result["data"] is not None

    # Check bus count
    assert result["data"]["num_buses"] == 132  # Updated to match actual feeder

    # Verify feeder_id matches
    assert result["data"]["feeder_id"] == "IEEE123"


def test_invalid_feeder_id():
    """Test loading with an invalid feeder ID."""
    # Act
    result = load_ieee_test_feeder("IEEE999")

    # Assert response structure
    assert "success" in result
    assert result["success"] is False

    # Check errors
    assert "errors" in result
    assert result["errors"] is not None
    assert len(result["errors"]) > 0
    assert "unsupported feeder id" in "\n".join(result["errors"]).lower()

    # Data should be None on error
    assert result["data"] is None


def test_return_format():
    """Test the response format of the load_ieee_test_feeder function."""
    # Act
    result = load_ieee_test_feeder("IEEE13")

    # Assert top-level keys
    assert (
        set(result.keys()) == REQUIRED_RESPONSE_KEYS
    ), f"Response missing required keys. Expected {REQUIRED_RESPONSE_KEYS}, got {set(result.keys())}"

    # Assert success is boolean
    assert isinstance(result["success"], bool)

    # Check data structure on success
    if result["success"]:
        assert "data" in result
        assert result["data"] is not None

        # Check all required data fields are present
        data_keys = set(result["data"].keys())
        missing_keys = REQUIRED_DATA_KEYS - data_keys
        assert not missing_keys, f"Missing required data keys: {missing_keys}"

        # Check types of data fields
        assert isinstance(result["data"]["feeder_id"], str)
        assert isinstance(result["data"]["num_buses"], int)
        assert isinstance(result["data"]["num_lines"], int)
        assert isinstance(result["data"]["num_loads"], int)
        assert isinstance(result["data"]["num_transformers"], int)
        assert isinstance(result["data"]["total_load_kw"], (int, float))
        assert isinstance(result["data"]["total_load_kvar"], (int, float))
        assert isinstance(result["data"]["voltage_bases_kv"], list)
        assert isinstance(result["data"]["feeder_length_km"], (int, float))
    else:
        # On error, data should be None and errors should be present
        assert result["data"] is None
        assert isinstance(result["errors"], list)
        assert len(result["errors"]) > 0
        assert all(isinstance(e, str) for e in result["errors"])

    # Check metadata (can be None or dict)
    assert result["metadata"] is None or isinstance(result["metadata"], dict)
