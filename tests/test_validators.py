"""
Tests for the validators module.
"""

import pytest
from unittest.mock import MagicMock

from opendss_mcp.utils.validators import (
    validate_bus_id,
    validate_positive_float,
    validate_voltage_limits,
    validate_feeder_id,
    VALID_FEEDER_IDS,
    MIN_VOLTAGE_PU,
    MAX_VOLTAGE_PU,
)


class TestValidateBusId:
    """Tests for validate_bus_id function."""

    def test_valid_bus_id(self):
        """Test that a valid bus ID passes validation."""
        mock_circuit = MagicMock()
        mock_circuit.get_bus_names.return_value = ["bus1", "bus2", "bus3"]

        # Should not raise any exception
        validate_bus_id("bus1", mock_circuit)
        validate_bus_id("bus2", mock_circuit)
        validate_bus_id("bus3", mock_circuit)

    def test_invalid_bus_id(self):
        """Test that an invalid bus ID raises ValueError."""
        mock_circuit = MagicMock()
        mock_circuit.get_bus_names.return_value = ["bus1", "bus2", "bus3"]

        with pytest.raises(RuntimeError, match="Error validating bus ID"):
            validate_bus_id("invalid_bus", mock_circuit)

    def test_bus_validation_with_circuit_error(self):
        """Test that circuit errors are wrapped in RuntimeError."""
        mock_circuit = MagicMock()
        mock_circuit.get_bus_names.side_effect = Exception("Circuit error")

        with pytest.raises(RuntimeError, match="Error validating bus ID"):
            validate_bus_id("bus1", mock_circuit)

    def test_bus_id_error_message_includes_samples(self):
        """Test that error message includes sample buses."""
        mock_circuit = MagicMock()
        mock_circuit.get_bus_names.return_value = [
            "bus1",
            "bus2",
            "bus3",
            "bus4",
            "bus5",
            "bus6",
        ]

        with pytest.raises(RuntimeError, match="Error validating bus ID"):
            validate_bus_id("invalid", mock_circuit)


class TestValidatePositiveFloat:
    """Tests for validate_positive_float function."""

    def test_valid_positive_integers(self):
        """Test that positive integers pass validation."""
        validate_positive_float(1, "test_param")
        validate_positive_float(100, "test_param")
        validate_positive_float(1000000, "test_param")

    def test_valid_positive_floats(self):
        """Test that positive floats pass validation."""
        validate_positive_float(0.1, "test_param")
        validate_positive_float(1.5, "test_param")
        validate_positive_float(999.99, "test_param")

    def test_zero_raises_error(self):
        """Test that zero raises ValueError."""
        with pytest.raises(ValueError, match="must be a positive number"):
            validate_positive_float(0, "test_param")

    def test_negative_raises_error(self):
        """Test that negative values raise ValueError."""
        with pytest.raises(ValueError, match="must be a positive number"):
            validate_positive_float(-1, "test_param")

        with pytest.raises(ValueError, match="must be a positive number"):
            validate_positive_float(-0.5, "test_param")

    def test_non_numeric_raises_error(self):
        """Test that non-numeric values raise ValueError."""
        with pytest.raises(ValueError, match="must be a positive number"):
            validate_positive_float("100", "test_param")

        with pytest.raises(ValueError, match="must be a positive number"):
            validate_positive_float(None, "test_param")

    def test_error_message_includes_parameter_name(self):
        """Test that error message includes the parameter name."""
        with pytest.raises(ValueError, match="my_parameter must be a positive number"):
            validate_positive_float(-1, "my_parameter")


class TestValidateVoltageLimits:
    """Tests for validate_voltage_limits function."""

    def test_valid_voltage_limits(self):
        """Test that valid voltage limits pass validation."""
        validate_voltage_limits(0.9, 1.1)
        validate_voltage_limits(0.95, 1.05)
        validate_voltage_limits(MIN_VOLTAGE_PU, MAX_VOLTAGE_PU)
        validate_voltage_limits(0.85, 1.15)

    def test_min_equals_max_raises_error(self):
        """Test that min == max raises ValueError."""
        with pytest.raises(ValueError, match="Voltage limits must satisfy"):
            validate_voltage_limits(1.0, 1.0)

    def test_min_greater_than_max_raises_error(self):
        """Test that min > max raises ValueError."""
        with pytest.raises(ValueError, match="Voltage limits must satisfy"):
            validate_voltage_limits(1.1, 0.9)

    def test_min_below_absolute_min_raises_error(self):
        """Test that min < MIN_VOLTAGE_PU raises ValueError."""
        with pytest.raises(ValueError, match="Voltage limits must satisfy"):
            validate_voltage_limits(0.7, 1.1)

    def test_max_above_absolute_max_raises_error(self):
        """Test that max > MAX_VOLTAGE_PU raises ValueError."""
        with pytest.raises(ValueError, match="Voltage limits must satisfy"):
            validate_voltage_limits(0.9, 1.3)

    def test_both_limits_out_of_range(self):
        """Test that both limits out of range raises ValueError."""
        with pytest.raises(ValueError, match="Voltage limits must satisfy"):
            validate_voltage_limits(0.7, 1.3)


class TestValidateFeederID:
    """Tests for validate_feeder_id function."""

    def test_valid_feeder_ids(self):
        """Test that valid feeder IDs pass validation."""
        for feeder_id in VALID_FEEDER_IDS:
            validate_feeder_id(feeder_id)

    def test_invalid_feeder_id_raises_error(self):
        """Test that invalid feeder ID raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported feeder ID"):
            validate_feeder_id("IEEE999")

    def test_case_sensitive_validation(self):
        """Test that validation is case-sensitive."""
        with pytest.raises(ValueError, match="Unsupported feeder ID"):
            validate_feeder_id("ieee13")

        with pytest.raises(ValueError, match="Unsupported feeder ID"):
            validate_feeder_id("IEEE_13")

    def test_error_message_includes_valid_options(self):
        """Test that error message lists valid options."""
        with pytest.raises(ValueError, match="Valid options are"):
            validate_feeder_id("invalid")

        # Check that error message includes all valid feeder IDs
        try:
            validate_feeder_id("invalid")
        except ValueError as e:
            error_msg = str(e)
            for feeder_id in VALID_FEEDER_IDS:
                assert feeder_id in error_msg


class TestValidatorConstants:
    """Tests to verify validator constants are defined correctly."""

    def test_valid_feeder_ids_defined(self):
        """Test that VALID_FEEDER_IDS is a non-empty list."""
        assert isinstance(VALID_FEEDER_IDS, list)
        assert len(VALID_FEEDER_IDS) > 0
        assert all(isinstance(fid, str) for fid in VALID_FEEDER_IDS)

    def test_voltage_limits_defined(self):
        """Test that voltage limit constants are defined."""
        assert isinstance(MIN_VOLTAGE_PU, (int, float))
        assert isinstance(MAX_VOLTAGE_PU, (int, float))
        assert MIN_VOLTAGE_PU < MAX_VOLTAGE_PU
        assert MIN_VOLTAGE_PU > 0
        assert MAX_VOLTAGE_PU > 0
