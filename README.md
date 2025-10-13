# OpenDSS MCP Server

OpenDSS MCP Server is a Model Context Protocol (MCP) server that provides a conversational interface for EPRI's Open Distribution System Simulator (OpenDSS). It enables AI assistants like Claude to perform power systems analysis through natural language.

## Features
- Load IEEE test feeders (IEEE 13, 34, 123 bus systems)
- Run power flow analysis with convergence checking
- Analyze voltage profiles and power flows
- Calculate system losses and loading
- Built on official EPRI OpenDSS test cases

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Steps

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd opendss-mcp-server
   ```

2. **Install the package in development mode:**
   ```bash
   pip install -e .
   ```

3. **Download official IEEE test feeders:**
   ```bash
   python src/opendss_mcp/data/download_official_feeders.py
   ```

4. **Verify installation:**
   ```bash
   python examples/test_server.py
   ```

   You should see successful loading of IEEE13 feeder and power flow results.

## Configuration for Claude Desktop

To use this MCP server with Claude Desktop, you need to configure it in your Claude Desktop settings.

### macOS/Linux Configuration

1. **Locate your Claude Desktop config file:**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. **Edit the config file** and add the OpenDSS MCP server configuration:

   ```json
   {
     "mcpServers": {
       "opendss-mcp-server": {
         "command": "python",
         "args": ["-m", "opendss_mcp.server"],
         "cwd": "/absolute/path/to/opendss-mcp-server",
         "env": {
           "PYTHONPATH": "/absolute/path/to/opendss-mcp-server",
           "OPENDSS_LOG_LEVEL": "INFO"
         }
       }
     }
   }
   ```

3. **Update the paths:**
   - Replace `/absolute/path/to/opendss-mcp-server` with your actual installation path
   - For example: `/Users/username/projects/opendss-mcp-server`

4. **Restart Claude Desktop** for the changes to take effect.

### Windows Configuration

1. **Locate your Claude Desktop config file:**
   - `%APPDATA%\Claude\claude_desktop_config.json`

2. **Edit the config file** with the same JSON structure, using Windows-style paths:

   ```json
   {
     "mcpServers": {
       "opendss-mcp-server": {
         "command": "python",
         "args": ["-m", "opendss_mcp.server"],
         "cwd": "C:\\Users\\username\\projects\\opendss-mcp-server",
         "env": {
           "PYTHONPATH": "C:\\Users\\username\\projects\\opendss-mcp-server",
           "OPENDSS_LOG_LEVEL": "INFO"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**.

### Verification

After configuring Claude Desktop:

1. Open Claude Desktop
2. Look for the MCP server icon (🔌) indicating active servers
3. Try asking Claude: "Load the IEEE13 test feeder and run a power flow analysis"
4. Claude should be able to use the OpenDSS MCP tools to perform the analysis

## Usage

### Available MCP Tools

1. **`load_feeder`** - Load an IEEE test feeder
   - Parameters: `feeder_id` (IEEE13, IEEE34, or IEEE123)
   - Returns: Feeder metadata (buses, lines, loads, transformers, total load)

2. **`run_power_flow_analysis`** - Run power flow on loaded feeder
   - Parameters: `feeder_id`, optional `options` (max_iterations, tolerance, control_mode)
   - Returns: Convergence status, bus voltages, min/max voltages

### Example Conversations with Claude

**Example 1: Basic Analysis**
```
You: Load the IEEE13 test feeder and tell me about it.

Claude: [Uses load_feeder tool]
The IEEE13 feeder has been loaded successfully:
- 16 buses
- 12 lines
- 15 loads
- Total load: 3,466 kW and 2,102 kvar
- Feeder length: 8.20 km
```

**Example 2: Power Flow Analysis**
```
You: Run a power flow analysis on IEEE13 and check for voltage violations.

Claude: [Uses load_feeder and run_power_flow_analysis tools]
Power flow converged in 4 iterations. Voltage profile:
- Maximum voltage: 1.056 pu at bus RG60
- Minimum voltage: 0.961 pu at bus 611
- All voltages within acceptable range (0.95-1.05 pu)
- Bus 611 is slightly below the typical lower limit
```

### Direct Python Usage

You can also use the tools directly in Python:

```python
from opendss_mcp.tools.feeder_loader import load_ieee_test_feeder
from opendss_mcp.tools.power_flow import run_power_flow

# Load a feeder
result = load_ieee_test_feeder('IEEE13')
print(f"Loaded {result['data']['num_buses']} buses")

# Run power flow
pf_result = run_power_flow('IEEE13')
print(f"Converged: {pf_result['data']['converged']}")
print(f"Voltage range: {pf_result['data']['min_voltage']:.3f} - {pf_result['data']['max_voltage']:.3f} pu")
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run all tests
pytest

# Run with coverage
pytest --cov=src/opendss_mcp --cov-report=term-missing

# Run specific test file
pytest tests/test_feeder_loader.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
pylint src/opendss_mcp

# Type checking
mypy src/opendss_mcp
```

## Project Structure

```
opendss-mcp-server/
├── src/opendss_mcp/
│   ├── server.py              # MCP server entry point
│   ├── tools/                 # MCP tools
│   │   ├── feeder_loader.py   # IEEE feeder loading
│   │   └── power_flow.py      # Power flow analysis
│   ├── utils/                 # Utilities
│   │   ├── dss_wrapper.py     # OpenDSS wrapper
│   │   ├── validators.py      # Input validation
│   │   └── formatters.py      # Response formatting
│   └── data/                  # Test feeders and data
│       └── ieee_feeders/      # IEEE test feeder files
├── tests/                     # Test suite
├── examples/                  # Example scripts
├── pyproject.toml            # Project configuration
└── README.md                 # This file
```

## Troubleshooting

**Issue: "ModuleNotFoundError: No module named 'opendssdirect'"**
- Solution: Run `pip install -e .` to install dependencies

**Issue: "Feeder file not found"**
- Solution: Run the download script: `python src/opendss_mcp/data/download_official_feeders.py`

**Issue: Claude Desktop doesn't see the MCP server**
- Check that the `cwd` path in config is correct and absolute
- Ensure Python is in your PATH
- Check Claude Desktop logs for error messages
- Restart Claude Desktop after config changes

**Issue: "Power flow did not converge"**
- This usually indicates a problem with the circuit definition
- Try reloading the feeder with `load_feeder` tool
- Check OpenDSS logs for detailed error messages

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
