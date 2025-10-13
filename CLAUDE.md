# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenDSS MCP Server is a Model Context Protocol (MCP) server that provides a conversational interface for EPRI's Open Distribution System Simulator (OpenDSS). It enables AI assistants to perform power systems analysis through natural language.

**Mission:** Reduce distribution planning studies from 2-3 weeks to 30 minutes through conversational AI interaction.

**Target Users:** Distribution planning engineers, DER integration specialists, power systems consultants, utility planning departments, and researchers.

## Architecture

### Core Components

1. **MCP Server** (`src/opendss_mcp/server.py`)
   - Entry point for the MCP server
   - Registers tools using `@server.tool()` decorator
   - Runs with stdio transport: `server.run(transport='stdio')`
   - All tool handlers wrap underlying tool functions with error handling

2. **Tools Layer** (`src/opendss_mcp/tools/`)
   - Each tool is a standalone module that performs a specific OpenDSS operation
   - Tools return structured responses: `{success: bool, data: dict, metadata: dict, errors: list}`
   - Current tools: `feeder_loader.py` (loads IEEE test feeders), `power_flow.py` (runs power flow analysis)
   - Future tools: DER optimization, voltage violation checking, capacity analysis, time-series simulation, visualization

3. **Utils Layer** (`src/opendss_mcp/utils/`)
   - `dss_wrapper.py`: DSSCircuit class provides stateful wrapper around opendssdirect.py
   - `validators.py`: Input validation functions (feeder IDs, bus IDs, voltage limits, positive floats)
   - `formatters.py`: Response formatting utilities (success/error responses, voltage stats, line flow stats)

4. **Data Layer** (`src/opendss_mcp/data/`)
   - `ieee_feeders/`: IEEE 13, 34, and 123 bus test feeder DSS files
   - `load_profiles/`: Time-series load profiles for simulation (placeholder)
   - `control_curves/`: Volt-var and volt-watt curves for smart inverter control (placeholder)

### State Management

**Critical:** OpenDSS state is NOT persistent between tool calls. The DSSCircuit wrapper maintains minimal state (`current_feeder`, `dss_file_path`) but the underlying OpenDSS circuit may need to be reloaded.

### Tool Implementation Pattern

Every tool follows this structure:
1. **Validate inputs** using `validators.py` functions
2. **Check circuit state** (verify a circuit is loaded if required)
3. **Perform OpenDSS operations** with try-except error handling
4. **Format and return results** using `formatters.py` functions

Never raise exceptions to the MCP layer - always return error dictionaries.

## Development Commands

### Setup
```bash
pip install -e .                # Install in development mode
pip install -e ".[test]"        # Install with test dependencies
```

### Testing
```bash
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest --cov=src/opendss_mcp --cov-report=term-missing  # With coverage
pytest tests/test_power_flow.py # Run single test file
pytest -k test_name             # Run specific test
```

### Code Quality
```bash
black src/ tests/               # Format code
pylint src/opendss_mcp          # Lint (target score >8.0)
mypy src/opendss_mcp            # Type checking
```

### Running
```bash
python -m opendss_mcp.server    # Start MCP server
python examples/test_server.py  # Run example/test script
```

## Key Technical Details

### OpenDSS Integration (opendssdirect.py)

**Always wrap OpenDSS calls in try-except blocks:**
```python
try:
    dss.Solution.Solve()
    if not dss.Solution.Converged():
        return format_error_response("Power flow did not converge")
except Exception as e:
    return format_error_response(f"OpenDSS error: {str(e)}")
```

**Working directory matters:** When loading IEEE feeders, the code changes to the feeder directory before compiling DSS files (because DSS files use relative paths for includes). Always restore the original directory in a finally block.

**Getting voltages:** Use `dss.Circuit.SetActiveBus(bus_name)` then `dss.Bus.puVmagAngle()` which returns `[V1_mag, V1_ang, V2_mag, V2_ang, ...]` for all phases.

**Counting elements:** Must iterate with `First()` and `Next()` pattern - OpenDSS doesn't provide direct count for all element types.

### IEEE Feeder Configuration

Feeder files are organized in subdirectories. The `FEEDER_CONFIG` dict in `feeder_loader.py` maps IDs to file paths:
- IEEE13: `13Bus/IEEE13.dss`
- IEEE34: `34Bus/ieee34Mod1.dss`
- IEEE123: `123Bus/IEEE123Master.dss`

### Response Format

All tools return this structure:
```python
{
    "success": bool,
    "data": dict | None,      # Main results
    "metadata": dict | None,  # Optional metadata (computation time, versions, etc.)
    "errors": list[str] | None
}
```

### Type Hints

Use modern Python type hints (Python 3.10+):
- `dict[str, Any]` not `Dict[str, Any]`
- `list[str]` not `List[str]`
- `tuple[float, float]` not `Tuple[float, float]`
- Use `| None` instead of `Optional[]` when appropriate

## Code Style (from .cursorrules)

- **Line length:** 100 characters
- **Formatter:** black
- **Docstrings:** Google-style for all public functions
- **Constants:** UPPER_CASE
- **Variables:** descriptive_snake_case (e.g., `bus_voltages_pu`, `min_voltage_pu`)

## Critical Rules

### ALWAYS
- Return structured JSON responses with success/data/errors
- Validate inputs before OpenDSS operations
- Use type hints on all functions
- Write Google-style docstrings
- Handle OpenDSS errors gracefully (never raise to MCP layer)
- Use try-except-finally when changing directories

### NEVER
- Raise exceptions to MCP layer (return error dicts instead)
- Assume OpenDSS state persists between tool calls
- Use magic numbers (define constants)
- Skip input validation
- Hard-code file paths (use pathlib)

## Testing Strategy

- **Unit tests:** Test each tool independently with IEEE13 feeder
- **Integration tests:** Test complete workflows (load feeder → run power flow → check violations → optimize DER)
- **Performance tests:** Power flow should complete in <5 seconds for IEEE123 feeder
- **Coverage target:** >80% code coverage

Use `tests/test_feeders.py` as a reference for testing patterns.

## Common Pitfalls

1. **Directory changes:** DSS files use relative paths. Always `os.chdir()` to feeder directory before compiling, and restore in finally block.
2. **OpenDSS iterators:** Elements like Lines, Loads, Transformers require `First()` then loop with `Next()` - they don't support len() or iteration.
3. **Voltage array format:** `dss.Bus.puVmagAngle()` returns interleaved `[mag, angle, mag, angle, ...]` - extract magnitudes with `[::2]`.
4. **State assumptions:** Don't assume a circuit is loaded - always check `dss.Circuit.Name()` or verify state.
5. **Type conversions:** Some OpenDSS properties return single floats instead of lists - handle both cases.

## Planned Features (from .cursorrules)

The project aims to implement 7 core MCP tools:
1. ✅ `load_ieee_test_feeder` - Load IEEE 13/34/123 bus feeders
2. ✅ `run_power_flow` - Power flow with optional harmonics analysis
3. ⏳ `optimize_der_placement` - Find optimal DER location with volt-var control
4. ⏳ `check_voltage_violations` - Identify buses exceeding limits
5. ⏳ `analyze_feeder_capacity` - Determine max DER hosting capacity
6. ⏳ `run_time_series_simulation` - Multi-timestep simulation with profiles
7. ⏳ `generate_visualization` - Create plots and network diagrams

Harmonics and volt-var control are advanced features to be added in later phases.
