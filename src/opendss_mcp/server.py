"""
OpenDSS Modelica Connection Protocol (MCP) Server.

This module implements an MCP server for OpenDSS power system simulations,
providing tools for loading IEEE test feeders and running power flow analyses.
"""

import logging
import sys
from typing import Any, Dict, Optional

# MCP SDK imports
from mcp.server import Server

# Local imports
from .tools.feeder_loader import load_ieee_test_feeder
from .tools.power_flow import run_power_flow
from .tools.voltage_checker import check_voltage_violations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server(
    name="opendss-mcp-server",
    version="0.1.0",
    description="OpenDSS Modelica Connection Protocol (MCP) Server"
)


@server.tool()
def load_feeder(
    feeder_id: str,
    modifications: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Load an IEEE test feeder into the OpenDSS engine.

    Args:
        feeder_id: Identifier of the IEEE test feeder (e.g., 'IEEE13', 'IEEE34', 'IEEE123')
        modifications: Optional dictionary of modifications to apply to the feeder

    Returns:
        Dictionary containing the loaded feeder data and metadata
    """
    try:
        logger.info(f"Loading feeder: {feeder_id}")
        result = load_ieee_test_feeder(feeder_id, modifications or {})
        
        if not result.get('success', False):
            error_msg = result.get('errors', ['Unknown error loading feeder'])
            logger.error(f"Failed to load feeder {feeder_id}: {error_msg}")
            
        return result
        
    except Exception as e:
        error_msg = f"Error loading feeder {feeder_id}: {str(e)}"
        logger.exception(error_msg)
        return {
            'success': False,
            'data': None,
            'metadata': None,
            'errors': [error_msg]
        }


@server.tool()
def run_power_flow_analysis(
    feeder_id: str,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run power flow analysis on a loaded feeder.

    Args:
        feeder_id: Identifier of the IEEE test feeder
        options: Dictionary of power flow options
            - max_iterations: Maximum number of iterations (default: 100)
            - tolerance: Convergence tolerance (default: 0.0001)
            - control_mode: Control mode for the solution (default: 'snapshot')

    Returns:
        Dictionary containing power flow results and metadata
    """
    try:
        logger.info(f"Running power flow for feeder: {feeder_id}")
        result = run_power_flow(feeder_id, options or {})

        if not result.get('success', False):
            error_msg = result.get('errors', ['Unknown error running power flow'])
            logger.error(f"Power flow failed for {feeder_id}: {error_msg}")

        return result

    except Exception as e:
        error_msg = f"Error running power flow for {feeder_id}: {str(e)}"
        logger.exception(error_msg)
        return {
            'success': False,
            'data': None,
            'metadata': None,
            'errors': [error_msg]
        }


@server.tool()
def check_voltages(
    min_voltage_pu: float = 0.95,
    max_voltage_pu: float = 1.05,
    phase: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check all bus voltages against specified limits and identify violations.

    Args:
        min_voltage_pu: Minimum acceptable voltage in per-unit (default: 0.95)
        max_voltage_pu: Maximum acceptable voltage in per-unit (default: 1.05)
        phase: Optional phase filter ('1', '2', '3', or None for all phases)

    Returns:
        Dictionary containing violations list, summary statistics, and metadata
    """
    try:
        logger.info(f"Checking voltage violations with limits [{min_voltage_pu}, {max_voltage_pu}] pu")
        result = check_voltage_violations(min_voltage_pu, max_voltage_pu, phase)

        if not result.get('success', False):
            error_msg = result.get('errors', ['Unknown error checking voltages'])
            logger.error(f"Voltage check failed: {error_msg}")
        else:
            num_violations = result.get('data', {}).get('summary', {}).get('total_violations', 0)
            logger.info(f"Found {num_violations} voltage violations")

        return result

    except Exception as e:
        error_msg = f"Error checking voltage violations: {str(e)}"
        logger.exception(error_msg)
        return {
            'success': False,
            'data': None,
            'metadata': None,
            'errors': [error_msg]
        }


def main() -> None:
    """Start the MCP server with stdio transport."""
    try:
        logger.info("Starting OpenDSS MCP Server")
        server.run(transport='stdio')
    except Exception as e:
        logger.critical(f"Server error: {str(e)}", exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
