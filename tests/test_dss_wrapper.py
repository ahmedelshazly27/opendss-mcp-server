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

    @patch('opendss_mcp.utils.dss_wrapper.dss')
    def test_dss_circuit_initialization(self, mock_dss):
        """Test that DSSCircuit initializes with correct attributes."""
        # Setup mock
        mock_dss.Basic.NumCircuits.return_value = 0
        
        # Initialize circuit
        circuit = DSSCircuit()
        
        # Verify initialization
        assert circuit.current_feeder is None
        assert circuit.dss_file_path is None
        assert circuit.is_initialized() is True
        
        # Verify OpenDSS was called
        mock_dss.Basic.NumCircuits.assert_called_once()
        mock_dss.run_command.assert_called_once_with("Clear")

    @patch('opendss_mcp.utils.dss_wrapper.dss')
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

    @patch('opendss_mcp.utils.dss_wrapper.dss')
    def test_load_nonexistent_file(self, mock_dss):
        """Test that loading a non-existent file returns False."""
        # Setup mock to raise error on compile
        mock_dss.run_command.side_effect = Exception("File not found")
        
        # Initialize circuit
        circuit = DSSCircuit()
        
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
        with patch('opendss_mcp.utils.dss_wrapper.dss') as mock_dss:
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
