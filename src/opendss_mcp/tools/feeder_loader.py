"""
Feeder loading functionality for OpenDSS MCP.

This module provides tools to load and analyze official IEEE test feeders,
including metadata collection and basic circuit analysis.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import opendssdirect as dss

from ..utils.dss_wrapper import DSSCircuit
from ..utils.validators import validate_feeder_id
from ..utils.formatters import format_success_response, format_error_response

# Path to the IEEE feeders directory
FEEDERS_DIR = Path(__file__).parent.parent / "data" / "ieee_feeders"

# Mapping of feeder IDs to their respective file names and base directories
FEEDER_CONFIG = {
    "IEEE13": {
        "file": "IEEE13.dss",
        "base_dir": ""
    },
    "IEEE34": {
        "file": "IEEE34.dss",
        "base_dir": ""
    },
    "IEEE123": {
        "file": "IEEE123.dss",
        "base_dir": ""
    }
}


def _calculate_total_line_length() -> float:
    """Calculate the total length of all lines in the circuit in kilometers.
    
    Returns:
        Total line length in kilometers
    """
    total_length = 0.0
    dss.Lines.First()
    while True:
        # Convert from meters to kilometers
        total_length += dss.Lines.Length() / 1000.0
        if not dss.Lines.Next() > 0:
            break
    return total_length


def _get_voltage_bases() -> List[float]:
    """Get the voltage bases from the circuit.
    
    Returns:
        List of voltage bases in kV
    """
    try:
        # Get voltage bases and convert to kV
        voltage_bases = dss.Settings.VoltageBases()
        
        # Handle case where voltage_bases is a single float/int
        if isinstance(voltage_bases, (int, float)):
            return [voltage_bases / 1000.0]
            
        # Handle case where voltage_bases is a string (comma-separated values)
        if isinstance(voltage_bases, str):
            return [float(vb.strip()) / 1000.0 for vb in voltage_bases.split(',') if vb.strip()]
            
        # Handle case where voltage_bases is already an iterable
        return [float(vb) / 1000.0 for vb in voltage_bases]
        
    except Exception as e:
        raise RuntimeError(f"Error getting voltage bases: {str(e)}") from e


def _calculate_total_load() -> tuple[float, float]:
    """Calculate the total load in the circuit.
    
    Returns:
        Tuple of (total_kw, total_kvar)
    """
    try:
        total_kw = 0.0
        total_kvar = 0.0
        
        # Check if there are any loads
        if dss.Loads.Count() == 0:
            return 0.0, 0.0
            
        dss.Loads.First()
        while True:
            # Get kW and kvar values
            kw = dss.Loads.kW()
            kvar = dss.Loads.kvar()
            
            # Ensure values are iterable (some versions return a single float)
            if isinstance(kw, (int, float)):
                kw = [kw]
            if isinstance(kvar, (int, float)):
                kvar = [kvar]
                
            total_kw += sum(kw) if kw else 0.0
            total_kvar += sum(kvar) if kvar else 0.0
            
            if not dss.Loads.Next() > 0:
                break
        
        return total_kw, total_kvar
        
    except Exception as e:
        raise RuntimeError(f"Error calculating total load: {str(e)}") from e


def _count_elements(element_type: str) -> int:
    """Count the number of elements of a specific type in the circuit.
    
    Args:
        element_type: Type of element to count (e.g., 'Line', 'Load', 'Transformer')
        
    Returns:
        Number of elements of the specified type
    """
    try:
        count = 0
        element_map = {
            'line': dss.Lines,
            'load': dss.Loads,
            'transformer': dss.Transformers
        }
    
        element = element_map.get(element_type.lower())
        if not element:
            return 0
            
        element.First()
        while True:
            count += 1
            if not element.Next() > 0:
                break
        return count
    except Exception as e:
        raise RuntimeError(f"Error counting {element_type} elements: {str(e)}") from e


def load_ieee_test_feeder(
    feeder_id: str,
    modifications: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Load an IEEE test feeder and return its metadata.
    
    This function loads a standard IEEE test feeder, applies any specified
    modifications, and returns comprehensive metadata about the circuit.
    
    Args:
        feeder_id: Identifier for the IEEE test feeder (e.g., 'IEEE13', 'IEEE34')
        modifications: Optional dictionary of circuit modifications to apply
            after loading the base model. Currently not implemented.
            
    Returns:
        Dictionary containing:
            - success: Boolean indicating if the operation was successful
            - data: Dictionary containing circuit metadata on success
            - metadata: Additional metadata about the operation
            - errors: List of error messages if any occurred
            
    Example:
        >>> result = load_ieee_test_feeder('IEEE13')
        >>> if result['success']:
        ...     print(f"Loaded {result['data']['num_buses']} buses")
    """
    try:
        # Validate feeder ID
        validate_feeder_id(feeder_id)
        
        # Initialize DSS circuit
        dss_circuit = DSSCircuit()
        
        # Get the feeder configuration
        if feeder_id not in FEEDER_CONFIG:
            return format_error_response(f"Unsupported feeder ID: {feeder_id}")
            
        config = FEEDER_CONFIG[feeder_id]

        # Build feeder path - handle empty base_dir
        if config["base_dir"]:
            feeder_dir = FEEDERS_DIR / config["base_dir"]
        else:
            feeder_dir = FEEDERS_DIR

        feeder_file = feeder_dir / config["file"]

        if not feeder_file.exists():
            return format_error_response(f"Feeder file not found: {feeder_file}")

        # Clear any existing circuit
        dss.Text.Command('Clear')

        # Change to the feeder directory to handle relative paths in DSS files
        current_dir = Path.cwd()
        try:
            os.chdir(feeder_dir)
            # Load the feeder file with full path to ensure it's found
            dss.Text.Command(f'compile [{feeder_file.absolute()}]')
        except Exception as e:
            return format_error_response(f"Error loading feeder {feeder_id}: {str(e)}")
        finally:
            # Always restore the original directory
            os.chdir(current_dir)
        
        # Apply any modifications if provided
        if modifications:
            # TODO: Implement circuit modifications
            pass
        
        # Collect circuit metadata
        num_buses = dss.Circuit.NumBuses()
        num_lines = _count_elements('line')
        num_loads = _count_elements('load')
        num_transformers = _count_elements('transformer')
        total_kw, total_kvar = _calculate_total_load()
        voltage_bases = _get_voltage_bases()
        feeder_length = _calculate_total_line_length()
        
        # Prepare response data
        data = {
            'feeder_id': feeder_id,
            'num_buses': num_buses,
            'num_lines': num_lines,
            'num_loads': num_loads,
            'num_transformers': num_transformers,
            'total_load_kw': round(total_kw, 2),
            'total_load_kvar': round(total_kvar, 2),
            'voltage_bases_kv': [round(vb, 2) for vb in voltage_bases],
            'feeder_length_km': round(feeder_length, 2)
        }
        
        return format_success_response(data)
        
    except Exception as e:
        return format_error_response(str(e))
