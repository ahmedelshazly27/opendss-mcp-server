"""
Tests for the formatters module.
"""

import pytest

from opendss_mcp.utils.formatters import (
    format_success_response,
    format_error_response,
    format_voltage_results,
    format_line_flow_results,
)


class TestFormatSuccessResponse:
    """Tests for format_success_response function."""

    def test_success_with_dict_data(self):
        """Test formatting success response with dictionary data."""
        data = {"key1": "value1", "key2": 123}
        result = format_success_response(data)

        assert result["success"] is True
        assert result["data"] == data
        assert result["metadata"] == {}
        assert result["errors"] is None

    def test_success_with_list_data(self):
        """Test formatting success response with list data."""
        data = [1, 2, 3, "test"]
        result = format_success_response(data)

        assert result["success"] is True
        assert result["data"] == data
        assert result["errors"] is None

    def test_success_with_metadata(self):
        """Test formatting success response with metadata."""
        data = {"result": "ok"}
        metadata = {"timestamp": "2024-01-01", "version": "1.0"}
        result = format_success_response(data, metadata)

        assert result["success"] is True
        assert result["metadata"] == metadata

    def test_success_without_metadata(self):
        """Test that metadata defaults to empty dict."""
        result = format_success_response({"data": "test"})
        assert result["metadata"] == {}


class TestFormatErrorResponse:
    """Tests for format_error_response function."""

    def test_error_with_single_string(self):
        """Test formatting error response with single error message."""
        error_msg = "Something went wrong"
        result = format_error_response(error_msg)

        assert result["success"] is False
        assert result["data"] is None
        assert result["metadata"] is None
        assert result["errors"] == [error_msg]

    def test_error_with_list_of_errors(self):
        """Test formatting error response with multiple error messages."""
        errors = ["Error 1", "Error 2", "Error 3"]
        result = format_error_response(errors)

        assert result["success"] is False
        assert result["errors"] == errors

    def test_error_response_structure(self):
        """Test that error response has correct structure."""
        result = format_error_response("test error")

        assert "success" in result
        assert "data" in result
        assert "metadata" in result
        assert "errors" in result


class TestFormatVoltageResults:
    """Tests for format_voltage_results function."""

    def test_voltage_with_normal_data(self):
        """Test formatting voltage results with normal data."""
        voltages = {"bus1": 1.05, "bus2": 0.95, "bus3": 1.00, "bus4": 0.98}
        result = format_voltage_results(voltages)

        assert result["min"] == 0.95
        assert result["max"] == 1.05
        assert result["min_bus"] == "bus2"
        assert result["max_bus"] == "bus1"
        assert "avg" in result
        assert isinstance(result["avg"], float)

    def test_voltage_with_empty_dict(self):
        """Test formatting voltage results with empty dictionary."""
        result = format_voltage_results({})

        assert result["min"] == 0.0
        assert result["max"] == 0.0
        assert result["avg"] == 0.0
        assert result["min_bus"] == ""
        assert result["max_bus"] == ""

    def test_voltage_with_single_bus(self):
        """Test formatting voltage results with single bus."""
        voltages = {"bus1": 1.02}
        result = format_voltage_results(voltages)

        assert result["min"] == 1.02
        assert result["max"] == 1.02
        assert result["avg"] == 1.02
        assert result["min_bus"] == "bus1"
        assert result["max_bus"] == "bus1"

    def test_voltage_average_calculation(self):
        """Test that voltage average is calculated correctly."""
        voltages = {"bus1": 1.0, "bus2": 1.1, "bus3": 1.2}
        result = format_voltage_results(voltages)

        expected_avg = (1.0 + 1.1 + 1.2) / 3
        assert abs(result["avg"] - expected_avg) < 0.0001

    def test_voltage_result_rounding(self):
        """Test that average voltage is rounded to 4 decimal places."""
        voltages = {"bus1": 1.123456789}
        result = format_voltage_results(voltages)

        assert result["avg"] == 1.1235


class TestFormatLineFlowResults:
    """Tests for format_line_flow_results function."""

    def test_line_flow_with_normal_data(self):
        """Test formatting line flow results with normal data."""
        flows = {
            "line1": {"P": 100.5, "Q": 50.2, "loading": 75.5},
            "line2": {"P": 200.3, "Q": 80.1, "loading": 90.2},
            "line3": {"P": 50.0, "Q": 25.0, "loading": 45.0},
        }
        result = format_line_flow_results(flows)

        assert result["max_loading"] == 90.2
        assert result["max_loading_line"] == "line2"
        assert result["total_p"] == round(100.5 + 200.3 + 50.0, 2)
        assert result["total_q"] == round(50.2 + 80.1 + 25.0, 2)
        assert result["line_count"] == 3

    def test_line_flow_with_empty_dict(self):
        """Test formatting line flow results with empty dictionary."""
        result = format_line_flow_results({})

        assert result["max_loading"] == 0.0
        assert result["max_loading_line"] == ""
        assert result["total_p"] == 0.0
        assert result["total_q"] == 0.0
        assert result["line_count"] == 0

    def test_line_flow_with_single_line(self):
        """Test formatting line flow results with single line."""
        flows = {"line1": {"P": 123.45, "Q": 67.89, "loading": 55.5}}
        result = format_line_flow_results(flows)

        assert result["max_loading"] == 55.5
        assert result["max_loading_line"] == "line1"
        assert result["total_p"] == 123.45
        assert result["total_q"] == 67.89
        assert result["line_count"] == 1

    def test_line_flow_with_missing_keys(self):
        """Test that missing keys default to 0."""
        flows = {
            "line1": {"loading": 50.0},  # Missing P and Q
            "line2": {"P": 100.0},  # Missing Q and loading
        }
        result = format_line_flow_results(flows)

        assert result["max_loading"] == 50.0
        assert result["total_p"] == 100.0
        assert result["total_q"] == 0.0
        assert result["line_count"] == 2

    def test_line_flow_rounding(self):
        """Test that values are rounded to 2 decimal places."""
        flows = {"line1": {"P": 123.456789, "Q": 67.891234, "loading": 75.987654}}
        result = format_line_flow_results(flows)

        assert result["max_loading"] == 75.99
        assert result["total_p"] == 123.46
        assert result["total_q"] == 67.89

    def test_line_flow_finds_max_loading_correctly(self):
        """Test that max loading line is identified correctly."""
        flows = {
            "line1": {"P": 100, "Q": 50, "loading": 30.0},
            "line2": {"P": 200, "Q": 80, "loading": 95.5},
            "line3": {"P": 150, "Q": 60, "loading": 75.0},
        }
        result = format_line_flow_results(flows)

        assert result["max_loading_line"] == "line2"
        assert result["max_loading"] == 95.5
