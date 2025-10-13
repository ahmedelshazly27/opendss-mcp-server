"""
Test script for OpenDSS MCP Server functionality.

This script demonstrates how to use the OpenDSS MCP Server tools directly
without going through the MCP protocol. It's useful for manual testing
and development.

Usage:
    python examples/test_server.py
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the tools directly
from src.opendss_mcp.tools.feeder_loader import load_ieee_test_feeder
from src.opendss_mcp.tools.power_flow import run_power_flow

def print_header(title: str) -> None:
    """Print a formatted header for better output readability."""
    print("\n" + "=" * 80)
    print(f" {title}".ljust(80, "="))
    print("=" * 80)

def test_load_feeder() -> None:
    """Test loading the IEEE 13-bus feeder."""
    print_header("TEST 1: LOADING IEEE13 FEEDER")
    
    # Load the IEEE 13-bus feeder
    result = load_ieee_test_feeder('IEEE13')
    
    # Print the results
    if result.get('success'):
        data = result.get('data', {})
        print("✅ Successfully loaded feeder:")
        print(f"- Feeder ID: {data.get('feeder_id')}")
        print(f"- Number of buses: {data.get('num_buses')}")
        print(f"- Number of lines: {data.get('num_lines')}")
        print(f"- Number of loads: {data.get('num_loads')}")
        print(f"- Number of transformers: {data.get('num_transformers')}")
        print(f"- Total load: {data.get('total_load_kw'):.2f} kW, {data.get('total_load_kvar'):.2f} kvar")
        print(f"- Voltage bases: {data.get('voltage_bases_kv')} kV")
        print(f"- Feeder length: {data.get('feeder_length_km'):.2f} km")
        return data  # Return the data for further processing
    else:
        print("❌ Failed to load feeder:")
        for error in result.get('errors', ['Unknown error']):
            print(f"- {error}")
        return None

def test_power_flow(feeder_data: dict) -> None:
    """Test running power flow on the loaded feeder."""
    if not feeder_data:
        print("\nSkipping power flow test - no feeder data available")
        return
    
    print_header("TEST 2: RUNNING POWER FLOW")
    
    # Run power flow
    result = run_power_flow('IEEE13')
    
    # Print the results
    if result.get('success'):
        data = result.get('data', {})
        print("✅ Power flow completed successfully")
        print(f"- Converged: {data.get('converged', False)}")
        print(f"- Iterations: {data.get('iterations', 0)}")
        print(f"- Max voltage: {data.get('max_voltage', 0):.4f} pu")
        print(f"- Min voltage: {data.get('min_voltage', 0):.4f} pu")
        
        # Print bus voltages if available
        if 'bus_voltages' in data:
            print("\nBus Voltages (pu):")
            for bus, voltage in data['bus_voltages'].items():
                print(f"- {bus}: {voltage:.6f} pu")
    else:
        print("❌ Power flow failed:")
        for error in result.get('errors', ['Unknown error']):
            print(f"- {error}")

def main() -> int:
    """Run the test suite."""
    print("🚀 Starting OpenDSS MCP Server Test")
    print(f"Working directory: {os.getcwd()}")
    
    # Test loading the feeder
    feeder_data = None
    load_result = test_load_feeder()
    if load_result and isinstance(load_result, dict):
        # Only run power flow if feeder was loaded successfully
        test_power_flow(load_result)
    
    print("\n✅ Test completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
