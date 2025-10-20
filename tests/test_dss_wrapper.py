"""
Unit tests for the DSSCircuit wrapper class.

These tests verify the functionality of the DSSCircuit class methods
using mocks to simulate OpenDSS behavior.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from opendss_mcp.utils.dss_wrapper import DSSCircuit


class TestDSSCircuitInitialization:
    """Test cases for DSSCircuit initialization and basic functionality."""

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_dss_circuit_initialization(self, mock_dss):
        """Test that DSSCircuit initializes with correct attributes."""
        # Setup mock
        mock_dss.Basic.NumCircuits.return_value = 0
        mock_dss.Text.Command.return_value = ""

        # Initialize circuit
        circuit = DSSCircuit()

        # Verify initialization
        assert circuit.current_feeder is None
        assert circuit.dss_file_path is None
        assert circuit.is_initialized() is True

        # Verify OpenDSS was called
        mock_dss.Basic.NumCircuits.assert_called()
        mock_dss.Text.Command.assert_called_with("Clear")

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_dss_circuit_reset(self, mock_dss):
        """Test that reset() clears the circuit and resets attributes."""
        # Initialize circuit with some values
        circuit = DSSCircuit()
        circuit.current_feeder = "test_feeder"
        circuit.dss_file_path = "/path/to/file.dss"

        # Call reset
        result = circuit.reset()

        # Verify reset behavior
        assert result is True
        assert circuit.current_feeder is None
        assert circuit.dss_file_path is None
        mock_dss.run_command.assert_called_with("Clear")

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_load_nonexistent_file(self, mock_dss):
        """Test that loading a non-existent file returns False."""
        # Setup mock to allow initialization
        mock_dss.Basic.NumCircuits.return_value = 0
        mock_dss.Text.Command.side_effect = ["", Exception("File not found")]

        # Initialize circuit
        circuit = DSSCircuit()

        # Reset the side effect for subsequent calls
        mock_dss.Text.Command.side_effect = Exception("File not found")

        # Try to load non-existent file
        result = circuit.load_dss_file("/nonexistent/file.dss")

        # Verify result
        assert result is False
        assert circuit.dss_file_path is None


class TestDSSCircuitWithPatches:
    """Test cases that require more complex patching."""

    @pytest.fixture
    def mock_dss(self):
        """Create a mock for the dss module with common methods."""
        with patch("opendss_mcp.utils.dss_wrapper.dss") as mock_dss:
            # Setup basic mock behavior
            mock_dss.Basic.NumCircuits.return_value = 0
            mock_dss.run_command.return_value = ""

            # Mock for get_bus_names
            mock_dss.Circuit.SetActiveBus.return_value = None
            mock_dss.Bus.AllBusNames.return_value = ["bus1", "bus2", "bus3"]

            # Mock for get_line_names
            mock_dss.ActiveClass.Count.return_value = 2
            mock_dss.Circuit.ActiveCktElement.Name.side_effect = ["line1", "line2"]

            yield mock_dss

    def test_get_bus_names(self, mock_dss):
        """Test that get_bus_names returns expected bus names."""
        circuit = DSSCircuit()
        bus_names = circuit.get_bus_names()

        assert isinstance(bus_names, list)
        assert bus_names == ["bus1", "bus2", "bus3"]
        mock_dss.Circuit.SetActiveBus.assert_called_once_with("*")
        mock_dss.Bus.AllBusNames.assert_called_once()

    def test_get_line_names(self, mock_dss):
        """Test that get_line_names returns expected line names."""
        circuit = DSSCircuit()
        line_names = circuit.get_line_names()

        assert isinstance(line_names, list)
        assert line_names == ["line1", "line2"]
        mock_dss.Circuit.SetActiveClass.assert_called_once_with("Line")
        assert mock_dss.ActiveClass.First.called
        assert mock_dss.ActiveClass.Next.called


class TestDSSCircuitPowerFlow:
    """Tests for power flow operations."""

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_solve_power_flow_success(self, mock_dss):
        """Test successful power flow solution."""
        mock_dss.Basic.NumCircuits.return_value = 0
        mock_dss.Text.Command.return_value = ""
        mock_dss.Solution.Solve.return_value = None
        mock_dss.Solution.Converged.return_value = True

        circuit = DSSCircuit()
        result = circuit.solve_power_flow()

        assert result is True
        mock_dss.Solution.Solve.assert_called_once()
        mock_dss.Solution.Converged.assert_called_once()

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_solve_power_flow_not_converged(self, mock_dss):
        """Test power flow that doesn't converge."""
        mock_dss.Basic.NumCircuits.return_value = 0
        mock_dss.Text.Command.return_value = ""
        mock_dss.Solution.Solve.return_value = None
        mock_dss.Solution.Converged.return_value = False

        circuit = DSSCircuit()
        result = circuit.solve_power_flow()

        assert result is False

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_solve_power_flow_error(self, mock_dss):
        """Test power flow with error."""
        mock_dss.Basic.NumCircuits.return_value = 0
        mock_dss.Text.Command.return_value = ""
        mock_dss.Solution.Solve.side_effect = Exception("Solver error")

        circuit = DSSCircuit()
        result = circuit.solve_power_flow()

        assert result is False


class TestDSSCircuitVoltages:
    """Tests for voltage operations."""

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_get_all_bus_voltages_success(self, mock_dss):
        """Test getting all bus voltages successfully."""
        mock_dss.Basic.NumCircuits.return_value = 0
        mock_dss.Text.Command.return_value = ""
        mock_dss.Circuit.SetActiveElement.return_value = None
        mock_dss.Circuit.Solution.Solve.return_value = None
        mock_dss.Circuit.SetActiveBus.return_value = None
        mock_dss.Bus.AllBusNames.return_value = ["bus1", "bus2"]
        mock_dss.Bus.puVmagAngle.side_effect = [
            [1.05, 0.0, 1.04, 120.0, 1.06, 240.0],  # bus1
            [0.95, 0.0, 0.96, 120.0, 0.94, 240.0],  # bus2
        ]

        circuit = DSSCircuit()
        voltages = circuit.get_all_bus_voltages()

        assert isinstance(voltages, dict)
        assert "bus1" in voltages
        assert "bus2" in voltages
        assert voltages["bus1"] == 1.06  # max of [1.05, 1.04, 1.06]
        assert voltages["bus2"] == 0.96  # max of [0.95, 0.96, 0.94]

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_get_all_bus_voltages_empty(self, mock_dss):
        """Test getting voltages when no buses exist."""
        mock_dss.Basic.NumCircuits.return_value = 0
        mock_dss.Text.Command.return_value = ""
        mock_dss.Bus.AllBusNames.return_value = []

        circuit = DSSCircuit()
        voltages = circuit.get_all_bus_voltages()

        assert voltages == {}

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_get_all_bus_voltages_error(self, mock_dss):
        """Test getting voltages with error."""
        mock_dss.Basic.NumCircuits.return_value = 0
        mock_dss.Text.Command.return_value = ""
        mock_dss.Circuit.SetActiveElement.side_effect = Exception("Circuit error")

        circuit = DSSCircuit()
        voltages = circuit.get_all_bus_voltages()

        assert voltages == {}


class TestDSSCircuitLineFlows:
    """Tests for line flow operations."""

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_get_all_line_flows_success(self, mock_dss):
        """Test getting all line flows successfully."""
        mock_dss.Basic.NumCircuits.return_value = 0
        mock_dss.Text.Command.return_value = ""
        mock_dss.Circuit.SetActiveClass.return_value = None
        mock_dss.ActiveClass.First.return_value = 1
        mock_dss.ActiveClass.Count.return_value = 2
        mock_dss.Circuit.ActiveCktElement.Name.side_effect = ["line1", "line2"]
        mock_dss.CktElement.Powers.side_effect = [
            [100.0, 50.0, 90.0, 45.0],  # line1: P1, Q1, P2, Q2
            [200.0, 80.0, 190.0, 75.0],  # line2
        ]
        mock_dss.Circuit.SetActiveElement.return_value = None
        mock_dss.CktElement.NormalAmps.side_effect = [400.0, 400.0]
        mock_dss.CktElement.CurrentsMagAng.side_effect = [
            [300.0, 0.0, 290.0, 120.0],  # line1 currents
            [350.0, 0.0, 340.0, 120.0],  # line2 currents
        ]
        mock_dss.ActiveClass.Next.return_value = 0

        circuit = DSSCircuit()
        flows = circuit.get_all_line_flows()

        assert isinstance(flows, dict)
        assert "line1" in flows
        assert "line2" in flows
        assert "P" in flows["line1"]
        assert "Q" in flows["line1"]
        assert "loading" in flows["line1"]

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_get_all_line_flows_error(self, mock_dss):
        """Test getting line flows with error."""
        mock_dss.Basic.NumCircuits.return_value = 0
        mock_dss.Text.Command.return_value = ""
        mock_dss.Circuit.SetActiveClass.side_effect = Exception("Circuit error")

        circuit = DSSCircuit()
        flows = circuit.get_all_line_flows()

        assert flows == {}


class TestDSSCircuitLosses:
    """Tests for loss operations."""

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_get_total_losses_success(self, mock_dss):
        """Test getting total losses successfully."""
        mock_dss.Basic.NumCircuits.return_value = 0
        mock_dss.Text.Command.return_value = ""
        mock_dss.Circuit.Losses.return_value = (123.45, 67.89)

        circuit = DSSCircuit()
        losses = circuit.get_total_losses()

        assert losses == (123.45, 67.89)
        mock_dss.Circuit.Losses.assert_called_once()

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_get_total_losses_error(self, mock_dss):
        """Test getting losses with error."""
        mock_dss.Basic.NumCircuits.return_value = 0
        mock_dss.Text.Command.return_value = ""
        mock_dss.Circuit.Losses.side_effect = Exception("Circuit error")

        circuit = DSSCircuit()
        losses = circuit.get_total_losses()

        assert losses == (0.0, 0.0)


class TestDSSCircuitErrorHandling:
    """Tests for error handling."""

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_initialization_failure(self, mock_dss):
        """Test initialization failure handling."""
        mock_dss.Basic.NumCircuits.side_effect = Exception("Init error")

        circuit = DSSCircuit()

        assert circuit.is_initialized() is False
        assert circuit.current_feeder is None
        assert circuit.dss_file_path is None

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_reset_failure(self, mock_dss):
        """Test reset failure handling."""
        mock_dss.Basic.NumCircuits.return_value = 0
        mock_dss.Text.Command.return_value = ""

        circuit = DSSCircuit()
        mock_dss.run_command.side_effect = Exception("Reset error")

        result = circuit.reset()
        assert result is False

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_get_bus_names_error(self, mock_dss):
        """Test get_bus_names error handling."""
        mock_dss.Basic.NumCircuits.return_value = 0
        mock_dss.Text.Command.return_value = ""
        mock_dss.Circuit.SetActiveBus.side_effect = Exception("Bus error")

        circuit = DSSCircuit()
        bus_names = circuit.get_bus_names()

        assert bus_names == []

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_get_line_names_error(self, mock_dss):
        """Test get_line_names error handling."""
        mock_dss.Basic.NumCircuits.return_value = 0
        mock_dss.Text.Command.return_value = ""
        mock_dss.Circuit.SetActiveClass.side_effect = Exception("Line error")

        circuit = DSSCircuit()
        line_names = circuit.get_line_names()

        assert line_names == []

    @patch("opendss_mcp.utils.dss_wrapper.dss")
    def test_load_dss_file_success(self, mock_dss):
        """Test successful DSS file loading."""
        mock_dss.Basic.NumCircuits.return_value = 0
        mock_dss.Text.Command.return_value = ""

        circuit = DSSCircuit()
        result = circuit.load_dss_file("/path/to/test.dss")

        assert result is True
        assert circuit.dss_file_path == "/path/to/test.dss"
