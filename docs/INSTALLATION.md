# Installation Guide

Complete installation guide for the OpenDSS MCP Server. This guide walks you through setting up the server, configuring Claude Desktop, and verifying everything works correctly.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Install OpenDSS](#install-opendss)
3. [Install OpenDSS MCP Server](#install-opendss-mcp-server)
4. [Configure Claude Desktop](#configure-claude-desktop)
5. [Verify Installation](#verify-installation)
6. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Software Requirements

- **Python 3.10 or later** (Python 3.11 or 3.12 recommended)
- **OpenDSS** (EPRI's Open Distribution System Simulator)
- **Git** (for cloning the repository)
- **Claude Desktop** (for conversational interface)

### Check Your Python Version

Open a terminal (macOS/Linux) or Command Prompt (Windows) and run:

```bash
python --version
```

Or:

```bash
python3 --version
```

You should see `Python 3.10.x` or higher. If not, download Python from [python.org](https://www.python.org/downloads/).

---

## Install OpenDSS

OpenDSS installation varies by operating system. Follow the instructions for your platform.

### Windows

**Option 1: Official Installer (Recommended)**

1. Download the official OpenDSS installer from:
   - [EPRI OpenDSS Downloads](https://sourceforge.net/projects/electricdss/)
   - Look for `OpenDSSSetup.exe` (latest version)

2. Run the installer and follow the prompts
   - Accept the license agreement
   - Use default installation path: `C:\Program Files\OpenDSS`
   - Complete the installation

3. Verify installation:
   ```cmd
   "C:\Program Files\OpenDSS\x64\OpenDSS.exe"
   ```

   You should see the OpenDSS console window open.

**Option 2: Python Package Only**

If you only need the Python interface (not the full OpenDSS suite):

```bash
pip install OpenDSSDirect.py
```

### macOS

**Using Homebrew (Recommended)**

1. Install Homebrew if you haven't already:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Install OpenDSS dependencies:
   ```bash
   brew install gcc
   brew install cmake
   ```

3. Install OpenDSSDirect.py (Python interface):
   ```bash
   pip3 install OpenDSSDirect.py
   ```

**Building from Source (Advanced)**

For the full OpenDSS engine on macOS, you'll need to build from source:

```bash
# Clone OpenDSS repository
git clone https://github.com/dss-extensions/dss_capi.git
cd dss_capi

# Build and install
mkdir build && cd build
cmake ..
make
sudo make install
```

Then install the Python interface:
```bash
pip3 install OpenDSSDirect.py
```

### Linux (Ubuntu/Debian)

1. Install build dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install -y build-essential gfortran cmake
   ```

2. Install OpenDSSDirect.py:
   ```bash
   pip3 install OpenDSSDirect.py
   ```

### Linux (Fedora/RHEL/CentOS)

1. Install build dependencies:
   ```bash
   sudo dnf install -y gcc gcc-gfortran cmake
   ```

2. Install OpenDSSDirect.py:
   ```bash
   pip3 install OpenDSSDirect.py
   ```

### Verify OpenDSS Installation

Test that OpenDSS is accessible from Python:

```bash
python3 -c "import opendssdirect as dss; print(f'OpenDSS version: {dss.Basic.Version()}')"
```

Expected output:
```
OpenDSS version: 9.x.x.x
```

If you see an error, refer to the [Troubleshooting](#troubleshooting) section.

---

## Install OpenDSS MCP Server

### Step 1: Clone the Repository

Navigate to where you want to install the server (e.g., `~/projects` or `C:\Users\YourName\projects`):

```bash
# Navigate to your projects directory
cd ~/projects           # macOS/Linux
cd C:\Users\YourName\projects   # Windows

# Clone the repository
git clone https://github.com/ahmedelshazly27/opendss-mcp-server.git

# Navigate into the directory
cd opendss-mcp-server
```

### Step 2: Install the Package

Install the server in **development mode** (recommended for updates):

```bash
pip install -e .
```

Or install normally:

```bash
pip install .
```

**For development with testing tools:**

```bash
pip install -e ".[test]"
```

This installs the server along with pytest, coverage, and other testing tools.

### Step 3: Verify Installation

Check that the server is installed correctly:

```bash
python -c "from opendss_mcp import server; print('OpenDSS MCP Server installed successfully!')"
```

Expected output:
```
OpenDSS MCP Server installed successfully!
```

---

## Configure Claude Desktop

The OpenDSS MCP Server integrates with Claude Desktop through the Model Context Protocol (MCP). Follow these steps to connect them.

### Step 1: Locate Claude Desktop Config File

The configuration file location depends on your operating system:

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### Step 2: Create or Edit Config File

If the file doesn't exist, create it. If it exists, you'll add to the `mcpServers` section.

**Full Configuration Example:**

```json
{
  "mcpServers": {
    "opendss": {
      "command": "python",
      "args": [
        "-m",
        "opendss_mcp.server"
      ],
      "env": {
        "PYTHONPATH": "/Users/yourusername/projects/opendss-mcp-server/src"
      }
    }
  }
}
```

**Important:** Replace `/Users/yourusername/projects/opendss-mcp-server/src` with the **absolute path** to your installation.

### Step 3: Find Your Absolute Path

**macOS/Linux:**
```bash
cd ~/projects/opendss-mcp-server
pwd
```

This outputs something like `/Users/ahmedelshazly/projects/opendss-mcp-server`. Append `/src` to get the full path.

**Windows:**
```cmd
cd C:\Users\YourName\projects\opendss-mcp-server
cd
```

This outputs something like `C:\Users\YourName\projects\opendss-mcp-server`. Append `\src` to get the full path.

### Step 4: Complete Configuration

**macOS/Linux Example:**

```json
{
  "mcpServers": {
    "opendss": {
      "command": "python3",
      "args": [
        "-m",
        "opendss_mcp.server"
      ],
      "env": {
        "PYTHONPATH": "/Users/ahmedelshazly/projects/opendss-mcp-server/src"
      }
    }
  }
}
```

**Windows Example:**

```json
{
  "mcpServers": {
    "opendss": {
      "command": "python",
      "args": [
        "-m",
        "opendss_mcp.server"
      ],
      "env": {
        "PYTHONPATH": "C:\\Users\\YourName\\projects\\opendss-mcp-server\\src"
      }
    }
  }
}
```

**Note:** On Windows, use double backslashes (`\\`) in paths.

### Step 5: Restart Claude Desktop

1. Quit Claude Desktop completely (not just close the window)
2. Reopen Claude Desktop
3. The MCP server should now be available

---

## Verify Installation

### Test 1: Check MCP Server Registration

In Claude Desktop, start a new conversation and type:

```
List all available MCP tools
```

You should see the 7 OpenDSS tools:
1. `load_feeder` - Load IEEE test feeders
2. `run_power_flow_analysis` - Run power flow analysis
3. `check_voltages` - Check voltage violations
4. `analyze_capacity` - Analyze DER hosting capacity
5. `optimize_der` - Optimize DER placement
6. `run_timeseries` - Run time-series simulation
7. `create_visualization` - Generate visualizations

### Test 2: Load a Test Feeder

In Claude Desktop, try:

```
Load the IEEE13 test feeder and tell me how many buses it has
```

Expected response should indicate that the IEEE13 feeder was successfully loaded with bus count information.

### Test 3: Run Power Flow

In Claude Desktop, try:

```
Run a power flow analysis on the IEEE13 feeder and show me the voltage range
```

Expected response should show successful power flow convergence and voltage statistics.

### Test 4: Generate Visualization

In Claude Desktop, try:

```
Generate a voltage profile visualization for the current circuit
```

Expected response should include a voltage profile plot showing bus voltages.

---

## Troubleshooting

### Issue 1: "OpenDSS not found" or Import Error

**Error message:**
```
ModuleNotFoundError: No module named 'opendssdirect'
```

**Solution:**

Install OpenDSSDirect.py:
```bash
pip install OpenDSSDirect.py
```

Or if using Python 3:
```bash
pip3 install OpenDSSDirect.py
```

**Verify installation:**
```bash
python3 -c "import opendssdirect as dss; print(dss.Basic.Version())"
```

---

### Issue 2: Claude Desktop Can't Find MCP Server

**Error in Claude Desktop:**
```
Failed to connect to MCP server: opendss
```

**Solutions:**

1. **Check Python path in config:**

   Ensure the `command` field uses the correct Python executable:
   ```bash
   which python3  # macOS/Linux
   where python   # Windows
   ```

   Update your config to use the full path if needed:
   ```json
   {
     "mcpServers": {
       "opendss": {
         "command": "/usr/local/bin/python3",
         "args": ["-m", "opendss_mcp.server"]
       }
     }
   }
   ```

2. **Check PYTHONPATH:**

   Verify the path in the config file points to the correct location:
   ```bash
   ls /Users/yourusername/projects/opendss-mcp-server/src/opendss_mcp/server.py
   ```

   The file should exist at this path.

3. **Check Claude Desktop logs:**

   **macOS:**
   ```bash
   tail -f ~/Library/Logs/Claude/mcp*.log
   ```

   **Windows:**
   ```cmd
   type %APPDATA%\Claude\Logs\mcp*.log
   ```

---

### Issue 3: Module Not Found Errors

**Error message:**
```
ModuleNotFoundError: No module named 'opendss_mcp'
```

**Solutions:**

1. **Reinstall the package:**
   ```bash
   cd ~/projects/opendss-mcp-server
   pip install -e .
   ```

2. **Check PYTHONPATH in Claude config:**

   Ensure the `env.PYTHONPATH` points to the `src` directory:
   ```json
   "env": {
     "PYTHONPATH": "/full/path/to/opendss-mcp-server/src"
   }
   ```

3. **Verify Python can import the module:**
   ```bash
   python3 -c "from opendss_mcp import server; print('Success')"
   ```

---

### Issue 4: Permission Denied Errors

**Error on macOS/Linux:**
```
PermissionError: [Errno 13] Permission denied
```

**Solutions:**

1. **Don't use sudo with pip:**
   ```bash
   pip install --user -e .
   ```

2. **Use a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   pip install -e .
   ```

---

### Issue 5: Tests Fail After Installation

**Error when running pytest:**
```
ImportError: cannot import name 'load_ieee_test_feeder'
```

**Solutions:**

1. **Install with test dependencies:**
   ```bash
   pip install -e ".[test]"
   ```

2. **Run tests from project root:**
   ```bash
   cd ~/projects/opendss-mcp-server
   pytest
   ```

3. **Check test data exists:**
   ```bash
   ls src/opendss_mcp/data/ieee_feeders/
   ```

   You should see directories for `13Bus`, `34Bus`, and `123Bus`.

---

### Issue 6: OpenDSS Version Conflicts

**Error:**
```
OpenDSS version mismatch or compatibility issues
```

**Solutions:**

1. **Update OpenDSSDirect.py:**
   ```bash
   pip install --upgrade OpenDSSDirect.py
   ```

2. **Check installed version:**
   ```bash
   pip show OpenDSSDirect.py
   ```

   Should be version 0.8.0 or later.

3. **If using Windows with full OpenDSS:**

   Ensure the Windows OpenDSS installation is version 9.0 or later.

---

### Issue 7: Matplotlib Display Issues

**Error:**
```
RuntimeError: main thread is not in main loop
```

**Solutions:**

1. **Set matplotlib backend (for macOS):**
   ```bash
   export MPLBACKEND=Agg
   ```

   Add this to your Claude Desktop config:
   ```json
   "env": {
     "PYTHONPATH": "/path/to/opendss-mcp-server/src",
     "MPLBACKEND": "Agg"
   }
   ```

2. **Install matplotlib dependencies:**
   ```bash
   pip install --upgrade matplotlib pillow
   ```

---

## Getting Help

If you encounter issues not covered here:

1. **Check GitHub Issues:**
   - [https://github.com/ahmedelshazly27/opendss-mcp-server/issues](https://github.com/ahmedelshazly27/opendss-mcp-server/issues)

2. **View Server Logs:**
   - MCP server logs are written to stderr
   - Check Claude Desktop logs for connection issues

3. **Run Server Manually:**
   ```bash
   python -m opendss_mcp.server
   ```

   This starts the server in stdio mode. You should see:
   ```
   INFO - Starting OpenDSS MCP Server
   ```

4. **Submit a Bug Report:**
   - Include your OS, Python version, and OpenDSS version
   - Attach error messages and logs
   - Describe steps to reproduce the issue

---

## Next Steps

Now that you have the OpenDSS MCP Server installed and configured:

1. **Try the Examples:**
   ```bash
   cd examples
   python generate_plots.py
   ```

2. **Read the Documentation:**
   - See `examples/README.md` for usage examples
   - See `README.md` for tool descriptions

3. **Run the Tests:**
   ```bash
   pytest -v
   ```

4. **Start Using Claude:**
   - Ask Claude to load a feeder and run power flow
   - Request voltage violation checks
   - Optimize DER placement
   - Generate visualizations

Happy power system analysis! ⚡
