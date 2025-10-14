# OpenDSS MCP Server - Examples

This directory contains example scripts demonstrating the visualization capabilities of the OpenDSS MCP Server.

## Visualization Examples

### generate_plots.py

This script demonstrates all 5 visualization types supported by the OpenDSS MCP Server by:
1. Loading the IEEE 13 Bus test feeder
2. Running power flow analysis
3. Performing DER hosting capacity analysis
4. Generating all visualization types
5. Saving example plots to `examples/plots/`

**Usage:**
```bash
python examples/generate_plots.py
```

**Generated Plots:**

1. **01_voltage_profile.png** - Bar chart showing voltage magnitudes at all buses
   - Color-coded by voltage level (green=normal, orange=warning, red=violation)
   - Includes ANSI voltage limits (0.95-1.05 pu)
   - Useful for identifying voltage regulation issues

2. **02_network_diagram.png** - Network topology diagram using networkx
   - Nodes colored by voltage level
   - Shows connectivity between buses
   - Useful for understanding feeder structure

3. **03_timeseries.png** - Multi-panel time-series plots
   - Shows load profile, losses, and voltage statistics over 24 hours
   - Demonstrates time-varying analysis capabilities
   - Useful for daily operational planning

4. **04_capacity_curve.png** - DER hosting capacity curve
   - Shows how line loading changes with increasing DER capacity
   - Identifies hosting capacity limits
   - Useful for planning distributed generation interconnections

5. **05_harmonics_spectrum.png** - Harmonic voltage spectrum
   - Bar charts showing harmonic magnitudes at selected buses
   - Includes THD (Total Harmonic Distortion) values
   - Useful for power quality analysis

## Plot Customization

All visualization functions support extensive customization through the `options` parameter:

```python
from opendss_mcp.tools.visualization import generate_visualization

# Example: Custom voltage profile
result = generate_visualization(
    plot_type="voltage_profile",
    data_source="circuit",
    options={
        "save_path": "my_voltage_profile.png",
        "title": "Custom Voltage Profile",
        "figsize": (16, 8),
        "dpi": 300,  # High resolution
        "show_violations": True,
        "bus_filter": ["650", "632", "671"]  # Plot only specific buses
    }
)
```

### Common Options

- `save_path`: Path to save plot file (if None, returns base64-encoded image)
- `title`: Custom plot title
- `figsize`: Tuple of (width, height) in inches
- `dpi`: Resolution in dots per inch (default: 100, use 300 for publication quality)
- `show_grid`: Whether to show grid lines (default: True)
- `show_violations`: Highlight voltage violations with color coding (default: True)
- `bus_filter`: List of specific buses to include in the plot (None = all buses)

### Plot-Specific Options

**Voltage Profile:**
- `min_voltage`: Minimum voltage limit (default: 0.95 pu)
- `max_voltage`: Maximum voltage limit (default: 1.05 pu)

**Network Diagram:**
- `layout`: Layout algorithm - "spring", "kamada_kawai", or "circular" (default: "spring")

**Time-Series:**
- `variables`: List of variables to plot (e.g., ["losses_kw", "min_voltage_pu"])
- `xlabel`: X-axis label (default: "Hour")
- `ylabel`: Y-axis label (default: "Value")

**Harmonics Spectrum:**
- `bus_filter`: List of buses to show harmonic spectra (default: worst THD bus)

## Data Sources

Visualizations can be generated from multiple data sources:

- `"circuit"`: Query current OpenDSS circuit state
- `"last_power_flow"`: Use most recent power flow results
- `"last_timeseries"`: Use most recent time-series simulation
- `"last_capacity"`: Use most recent capacity analysis
- `"last_harmonics"`: Use most recent harmonics analysis

Example:
```python
# Use stored harmonics data
result = generate_visualization(
    plot_type="harmonics_spectrum",
    data_source="last_harmonics",
    options={"save_path": "harmonics.png"}
)
```

## Output Formats

Visualizations can be:

1. **Saved to file** (if `save_path` is provided):
   - Returns file path in response
   - Supports PNG, PDF, SVG formats (inferred from file extension)
   - Default DPI: 100, recommended for publication: 300

2. **Encoded as base64** (if `save_path` is None):
   - Returns base64-encoded PNG image string
   - Useful for web APIs and embedding in HTML/JSON responses
   - Can be decoded with: `base64.b64decode(image_base64)`

## Integration with MCP Server

When using the MCP server, the visualization tool is available as `create_visualization`:

```python
# Through MCP server
result = server.create_visualization(
    plot_type="voltage_profile",
    data_source="circuit",
    options={"save_path": "/tmp/voltage.png"}
)

if result['success']:
    print(f"Plot saved to: {result['data']['file_path']}")
```

## Requirements

The visualization module requires:
- `matplotlib>=3.7.0`
- `networkx>=3.1`
- `numpy>=1.24.0`

These are automatically installed with the package.

## Additional Examples

See also:
- `test_server.py` - Basic MCP server usage examples
- `../tests/` - Unit tests demonstrating tool usage
