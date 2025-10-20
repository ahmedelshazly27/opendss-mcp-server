# OpenDSS MCP Server - Package Summary

## Package Information

**Name**: `opendss-mcp-server`
**Version**: 1.0.0
**License**: MIT
**Python**: ≥3.10

## Installation

### From PyPI (when published)
```bash
pip install opendss-mcp-server
```

### Development Installation
```bash
# Clone repository
git clone https://github.com/ahmedelshazly27/opendss-mcp-server.git
cd opendss-mcp-server

# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Install with all optional dependencies
pip install -e ".[all]"
```

## Package Structure

```
opendss-mcp-server/
├── src/opendss_mcp/
│   ├── server.py                 # MCP server entry point
│   ├── tools/                    # 7 MCP tools
│   │   ├── feeder_loader.py      # Load IEEE test feeders
│   │   ├── power_flow.py         # Power flow analysis
│   │   ├── der_optimizer.py      # DER placement optimization
│   │   ├── voltage_checker.py    # Voltage violation detection
│   │   ├── capacity.py           # Hosting capacity analysis
│   │   ├── timeseries.py         # Time-series simulation
│   │   └── visualization.py      # Plot generation
│   ├── utils/                    # Utility modules
│   │   ├── dss_wrapper.py        # OpenDSS wrapper
│   │   ├── validators.py         # Input validation
│   │   ├── formatters.py         # Response formatting
│   │   ├── harmonics.py          # Harmonic analysis
│   │   └── inverter_control.py   # Smart inverter control
│   └── data/                     # Data files
│       ├── ieee_feeders/         # IEEE test feeders
│       ├── load_profiles/        # Load profile templates
│       └── control_curves/       # Inverter curves
├── tests/                        # 220 tests (78% coverage)
├── examples/                     # Usage examples
├── docs/                         # Documentation
└── verify_complete.sh            # Verification script
```

## Dependencies

### Core Dependencies
- `mcp>=0.9.0` - Model Context Protocol
- `opendssdirect.py>=0.8.4` - OpenDSS Python interface
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical computing
- `matplotlib>=3.7.0` - Visualization
- `networkx>=3.1` - Network diagrams

### Optional Dependencies

**Development** (`pip install opendss-mcp-server[dev]`):
- pytest>=7.4.0
- pytest-cov>=4.1.0
- black>=23.0.0
- pylint>=2.17.0
- mypy>=1.4.0

**Testing** (`pip install opendss-mcp-server[test]`):
- pytest>=7.4.0
- pytest-cov>=4.1.0
- pytest-anyio>=0.0.0

**Documentation** (`pip install opendss-mcp-server[docs]`):
- sphinx>=7.0.0
- sphinx-rtd-theme>=1.3.0

## Project URLs

- **Homepage**: https://github.com/ahmedelshazly27/opendss-mcp-server
- **Documentation**: https://github.com/ahmedelshazly27/opendss-mcp-server#readme
- **Repository**: https://github.com/ahmedelshazly27/opendss-mcp-server
- **Bug Tracker**: https://github.com/ahmedelshazly27/opendss-mcp-server/issues
- **Changelog**: https://github.com/ahmedelshazly27/opendss-mcp-server/releases

## Quality Metrics

- **Tests**: 220 passing
- **Coverage**: 78%
- **Code Quality**: 8.38/10 (pylint)
- **Code Style**: Black formatted
- **Type Hints**: Comprehensive

## Performance

All operations exceed performance targets by >1000x:

| Operation | Target | Actual |
|-----------|--------|--------|
| Power Flow (IEEE123) | <5s | ~0.3ms |
| DER Optimization (10 buses) | <30s | ~5ms |
| Time-Series (24h) | <60s | ~1.5ms |

## Features

### 7 MCP Tools

1. **load_ieee_test_feeder** - Load IEEE 13/34/123 bus test feeders
2. **run_power_flow** - Power flow analysis with optional harmonics
3. **optimize_der_placement** - DER placement with volt-var control
4. **check_voltage_violations** - Voltage violation detection
5. **analyze_feeder_capacity** - Hosting capacity analysis
6. **run_time_series_simulation** - Multi-timestep simulation
7. **generate_visualization** - Network diagrams and plots

### Key Capabilities

- ✅ IEEE test feeder support (13, 34, 123 bus)
- ✅ Power flow analysis with harmonics
- ✅ DER optimization (solar, battery, wind, EV)
- ✅ Volt-var and volt-watt control (IEEE 1547, Rule 21)
- ✅ Voltage violation detection
- ✅ Hosting capacity analysis
- ✅ Time-series simulation
- ✅ Network visualization
- ✅ Harmonic analysis (THD)

## Supported Platforms

- ✅ Linux
- ✅ macOS
- ✅ Windows

## Python Versions

- ✅ Python 3.10
- ✅ Python 3.11
- ✅ Python 3.12
- ✅ Python 3.13

## Keywords

power-systems, opendss, mcp, energy, distribution, electrical-engineering, power-flow, der, ai, claude

## Classifiers

- Development Status :: 5 - Production/Stable
- Intended Audience :: Science/Research
- Intended Audience :: Developers
- Topic :: Scientific/Engineering
- Topic :: Scientific/Engineering :: Physics
- Programming Language :: Python :: 3.10+
- Operating System :: OS Independent
- Framework :: Pytest

## License

MIT License - See LICENSE file for details

## Author

Ahmed Elshazly <ahmedelshazly27@gmail.com>

## Contributing

See VERIFICATION.md for development workflow and PUBLISHING.md for release process.

## Support

- GitHub Issues: https://github.com/ahmedelshazly27/opendss-mcp-server/issues
- Documentation: See README.md and CLAUDE.md

---

**Mission**: Reduce distribution planning studies from 2-3 weeks to 30 minutes through conversational AI interaction.
