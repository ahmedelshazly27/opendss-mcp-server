"""
Response formatting utilities for OpenDSS MCP operations.

This module provides consistent response formatting for API responses,
including success/error responses and data transformations.
"""

from typing import Any, Dict, List, Optional, TypedDict, Union


class SuccessResponse(TypedDict):
    """Type definition for success response structure."""
    success: bool
    data: Union[Dict[str, Any], List[Any], None]
    metadata: Optional[Dict[str, Any]]
    errors: None


class ErrorResponse(TypedDict):
    """Type definition for error response structure."""
    success: bool
    data: None
    metadata: None
    errors: List[str]


class VoltageStats(TypedDict):
    """Type definition for voltage statistics."""
    min: float
    max: float
    avg: float
    min_bus: str
    max_bus: str


class LineFlowStats(TypedDict):
    """Type definition for line flow statistics."""
    max_loading: float
    max_loading_line: str
    total_p: float
    total_q: float
    line_count: int


def format_success_response(
    data: Union[Dict[str, Any], List[Any]],
    metadata: Optional[Dict[str, Any]] = None
) -> SuccessResponse:
    """Format a successful API response.

    Args:
        data: The main response data
        metadata: Optional additional metadata

    Returns:
        SuccessResponse: Formatted success response
    """
    return {
        "success": True,
        "data": data,
        "metadata": metadata or {},
        "errors": None
    }


def format_error_response(errors: Union[str, List[str]]) -> ErrorResponse:
    """Format an error response.

    Args:
        errors: Single error message or list of error messages

    Returns:
        ErrorResponse: Formatted error response
    """
    if isinstance(errors, str):
        errors = [errors]
    return {
        "success": False,
        "data": None,
        "metadata": None,
        "errors": errors
    }


def format_voltage_results(voltages: Dict[str, float]) -> Dict[str, Any]:
    """Calculate and format voltage statistics.

    Args:
        voltages: Dictionary mapping bus names to voltage magnitudes (p.u.)

    Returns:
        Dict containing voltage statistics
    """
    if not voltages:
        return {
            "min": 0.0,
            "max": 0.0,
            "avg": 0.0,
            "min_bus": "",
            "max_bus": ""
        }

    min_bus = min(voltages.items(), key=lambda x: x[1])
    max_bus = max(voltages.items(), key=lambda x: x[1])
    avg_voltage = sum(voltages.values()) / len(voltages)

    return {
        "min": min_bus[1],
        "max": max_bus[1],
        "avg": round(avg_voltage, 4),
        "min_bus": min_bus[0],
        "max_bus": max_bus[0]
    }


def format_line_flow_results(flows: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """Calculate and format line flow statistics.

    Args:
        flows: Dictionary mapping line names to flow information
              (must contain 'P', 'Q', and 'loading' keys)

    Returns:
        Dict containing line flow statistics
    """
    if not flows:
        return {
            "max_loading": 0.0,
            "max_loading_line": "",
            "total_p": 0.0,
            "total_q": 0.0,
            "line_count": 0
        }

    max_loading_line = max(flows.items(), key=lambda x: x[1].get('loading', 0))
    total_p = sum(flow.get('P', 0) for flow in flows.values())
    total_q = sum(flow.get('Q', 0) for flow in flows.values())

    return {
        "max_loading": round(max_loading_line[1].get('loading', 0), 2),
        "max_loading_line": max_loading_line[0],
        "total_p": round(total_p, 2),
        "total_q": round(total_q, 2),
        "line_count": len(flows)
    }
