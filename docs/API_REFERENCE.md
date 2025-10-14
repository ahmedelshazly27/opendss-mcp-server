# OpenDSS MCP Server - API Reference

Complete API reference for all MCP tools and utility functions.

**Version:** 1.0.0
**Last Updated:** October 14, 2025

---

## Table of Contents

### MCP Tools
1. [load_feeder](#1-load_feeder)
2. [run_power_flow_analysis](#2-run_power_flow_analysis)
3. [check_voltages](#3-check_voltages)
4. [analyze_capacity](#4-analyze_capacity)
5. [optimize_der](#5-optimize_der)
6. [run_timeseries](#6-run_timeseries)
7. [create_visualization](#7-create_visualization)

### Utility Functions
- [Validators](#validators)
- [Formatters](#formatters)
- [Harmonics Utilities](#harmonics-utilities)
- [Inverter Control Utilities](#inverter-control-utilities)

### Error Codes
- [Standard Error Codes](#error-codes)

---

## MCP Tools

All MCP tools follow a consistent response format:

```typescript
{
  success: boolean,           // Operation success status
  data: object | null,        // Result data (null on error)
  metadata: object | null,    // Additional metadata (null on error)
  errors: string[] | null     // Error messages (null on success)
}
```

---

## 1. load_feeder

Load an IEEE test feeder into the OpenDSS engine.

### Function Signature

```python
def load_feeder(
    feeder_id: str,
    modifications: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `feeder_id` | `string` | Yes | - | IEEE feeder identifier: `"IEEE13"`, `"IEEE34"`, or `"IEEE123"` |
| `modifications` | `dict` | No | `{}` | Optional modifications to apply (see Modifications section) |

#### Modifications Structure

```python
{
  "loads": {
    "<load_name>": {
      "kw_multiplier": float,    # Scale load real power
      "kvar_multiplier": float   # Scale load reactive power
    }
  },
  "capacitors": {
    "<cap_name>": {
      "bus": str,                # Bus to connect
      "kvar": float,             # Reactive power rating
      "phases": int              # Number of phases
    }
  },
  "lines": {
    "<line_name>": {
      "linecode": str,           # Line configuration
      "length": float            # Length in miles/km
    }
  }
}
```

### Return Format

```typescript
{
  success: boolean,
  data: {
    feeder_id: string,           // Feeder identifier
    num_buses: number,           // Number of buses in circuit
    num_lines: number,           // Number of lines
    num_transformers: number,    // Number of transformers
    num_loads: number,           // Number of loads
    num_capacitors: number,      // Number of capacitors
    num_regulators: number,      // Number of voltage regulators
    source_bus: string,          // Source bus name
    voltage_bases: number[],     // Voltage base values (kV)
    base_frequency: number,      // System frequency (Hz)
    dss_file_path: string        // Path to loaded DSS file
  },
  metadata: {
    timestamp: string,           // ISO 8601 timestamp
    execution_time_ms: number,   // Execution time
    opendss_version: string      // OpenDSS version
  },
  errors: null
}
```

### Example Request

```json
{
  "tool": "load_feeder",
  "parameters": {
    "feeder_id": "IEEE13",
    "modifications": {
      "loads": {
        "671": {
          "kw_multiplier": 1.2
        }
      },
      "capacitors": {
        "new_cap_675": {
          "bus": "675",
          "kvar": 300,
          "phases": 3
        }
      }
    }
  }
}
```

### Example Response (Success)

```json
{
  "success": true,
  "data": {
    "feeder_id": "IEEE13",
    "num_buses": 13,
    "num_lines": 11,
    "num_transformers": 1,
    "num_loads": 15,
    "num_capacitors": 1,
    "num_regulators": 1,
    "source_bus": "650",
    "voltage_bases": [115.0, 4.16],
    "base_frequency": 60.0,
    "dss_file_path": "/path/to/ieee_feeders/13Bus/IEEE13.dss"
  },
  "metadata": {
    "timestamp": "2025-10-14T10:30:00.000Z",
    "execution_time_ms": 245,
    "opendss_version": "9.8.0.1"
  },
  "errors": null
}
```

### Example Response (Error)

```json
{
  "success": false,
  "data": null,
  "metadata": null,
  "errors": [
    "Unsupported feeder ID: 'IEEE999'. Valid options are: \"IEEE13\", \"IEEE34\", \"IEEE123\""
  ]
}
```

### Error Codes

| Code | Message | Description |
|------|---------|-------------|
| `INVALID_FEEDER_ID` | Unsupported feeder ID: '{id}' | Feeder ID not in supported list |
| `DSS_FILE_NOT_FOUND` | DSS file not found at path: '{path}' | Feeder DSS file missing |
| `DSS_COMPILE_ERROR` | Failed to compile DSS file: {details} | OpenDSS compilation failure |
| `MODIFICATION_ERROR` | Error applying modifications: {details} | Invalid modification specification |

---

## 2. run_power_flow_analysis

Run power flow analysis on a loaded feeder.

### Function Signature

```python
def run_power_flow_analysis(
    feeder_id: str,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `feeder_id` | `string` | Yes | - | IEEE feeder identifier |
| `options` | `dict` | No | `{}` | Power flow options (see Options section) |

#### Options Structure

```python
{
  "max_iterations": int,       # Maximum iterations (default: 100)
  "tolerance": float,          # Convergence tolerance (default: 0.0001)
  "control_mode": str,         # Solution mode: "snapshot", "daily", "yearly" (default: "snapshot")
  "include_harmonics": bool    # Run harmonics analysis (default: false)
}
```

### Return Format

```typescript
{
  success: boolean,
  data: {
    converged: boolean,          // Did power flow converge?
    iterations: number,          // Number of iterations to converge
    min_voltage: number,         // Minimum voltage (pu)
    min_voltage_bus: string,     // Bus with minimum voltage
    max_voltage: number,         // Maximum voltage (pu)
    max_voltage_bus: string,     // Bus with maximum voltage
    total_losses_kw: number,     // Total real power losses (kW)
    total_losses_kvar: number,   // Total reactive power losses (kvar)
    num_buses: number,           // Number of buses in circuit
    num_nodes: number,           // Number of nodes (phases)
    solution_time_ms: number,    // OpenDSS solution time
    harmonics?: {                // Optional harmonics data
      enabled: boolean,
      buses_analyzed: string[],
      max_thd_pct: number,
      max_thd_bus: string
    }
  },
  metadata: {
    timestamp: string,
    execution_time_ms: number,
    feeder_id: string
  },
  errors: null
}
```

### Example Request

```json
{
  "tool": "run_power_flow_analysis",
  "parameters": {
    "feeder_id": "IEEE13",
    "options": {
      "max_iterations": 100,
      "tolerance": 0.0001,
      "control_mode": "snapshot",
      "include_harmonics": false
    }
  }
}
```

### Example Response (Success)

```json
{
  "success": true,
  "data": {
    "converged": true,
    "iterations": 8,
    "min_voltage": 0.9542,
    "min_voltage_bus": "675.3",
    "max_voltage": 1.0500,
    "max_voltage_bus": "650.1",
    "total_losses_kw": 116.2,
    "total_losses_kvar": 68.3,
    "num_buses": 13,
    "num_nodes": 36,
    "solution_time_ms": 45,
    "harmonics": {
      "enabled": false
    }
  },
  "metadata": {
    "timestamp": "2025-10-14T10:35:00.000Z",
    "execution_time_ms": 52,
    "feeder_id": "IEEE13"
  },
  "errors": null
}
```

### Example Response (Convergence Failure)

```json
{
  "success": false,
  "data": null,
  "metadata": null,
  "errors": [
    "Power flow did not converge after 100 iterations. Check circuit for modeling errors."
  ]
}
```

### Error Codes

| Code | Message | Description |
|------|---------|-------------|
| `NO_CIRCUIT_LOADED` | No circuit loaded. Load a feeder first. | No feeder has been loaded |
| `CONVERGENCE_FAILURE` | Power flow did not converge after {n} iterations | Solution did not converge |
| `SOLUTION_ERROR` | OpenDSS solution error: {details} | OpenDSS internal error |
| `INVALID_OPTION` | Invalid option: {option} | Unrecognized option parameter |

---

## 3. check_voltages

Check all bus voltages against specified limits and identify violations.

### Function Signature

```python
def check_voltages(
    min_voltage_pu: float = 0.95,
    max_voltage_pu: float = 1.05,
    phase: Optional[str] = None
) -> Dict[str, Any]
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `min_voltage_pu` | `float` | No | `0.95` | Minimum acceptable voltage (per-unit) |
| `max_voltage_pu` | `float` | No | `1.05` | Maximum acceptable voltage (per-unit) |
| `phase` | `string` | No | `null` | Filter by phase: `"1"`, `"2"`, `"3"`, or `null` for all |

### Return Format

```typescript
{
  success: boolean,
  data: {
    violations: Array<{
      bus: string,               // Bus name
      phase: string,             // Phase number
      voltage_pu: number,        // Actual voltage (pu)
      deviation_pu: number,      // Deviation from limit (pu)
      deviation_pct: number,     // Deviation percentage
      type: string               // "undervoltage" or "overvoltage"
    }>,
    summary: {
      total_violations: number,  // Total violation count
      undervoltage_count: number,// Undervoltage violations
      overvoltage_count: number, // Overvoltage violations
      buses_checked: number,     // Number of buses analyzed
      worst_undervoltage: number | null,  // Worst undervoltage (pu)
      worst_overvoltage: number | null,   // Worst overvoltage (pu)
      worst_undervoltage_bus: string | null,
      worst_overvoltage_bus: string | null
    },
    limits: {
      min_voltage_pu: number,
      max_voltage_pu: number
    }
  },
  metadata: {
    timestamp: string,
    execution_time_ms: number
  },
  errors: null
}
```

### Example Request

```json
{
  "tool": "check_voltages",
  "parameters": {
    "min_voltage_pu": 0.95,
    "max_voltage_pu": 1.05,
    "phase": null
  }
}
```

### Example Response (Success)

```json
{
  "success": true,
  "data": {
    "violations": [
      {
        "bus": "675",
        "phase": "3",
        "voltage_pu": 0.9542,
        "deviation_pu": -0.0458,
        "deviation_pct": -4.58,
        "type": "undervoltage"
      },
      {
        "bus": "634",
        "phase": "3",
        "voltage_pu": 0.9501,
        "deviation_pu": -0.0499,
        "deviation_pct": -4.99,
        "type": "undervoltage"
      }
    ],
    "summary": {
      "total_violations": 2,
      "undervoltage_count": 2,
      "overvoltage_count": 0,
      "buses_checked": 13,
      "worst_undervoltage": 0.9501,
      "worst_overvoltage": null,
      "worst_undervoltage_bus": "634.3",
      "worst_overvoltage_bus": null
    },
    "limits": {
      "min_voltage_pu": 0.95,
      "max_voltage_pu": 1.05
    }
  },
  "metadata": {
    "timestamp": "2025-10-14T10:40:00.000Z",
    "execution_time_ms": 23
  },
  "errors": null
}
```

### Error Codes

| Code | Message | Description |
|------|---------|-------------|
| `NO_CIRCUIT_LOADED` | No circuit loaded. Load and solve a feeder first. | No feeder loaded |
| `NO_SOLUTION` | No power flow solution available. Run power flow first. | Power flow not solved |
| `INVALID_LIMITS` | Voltage limits must satisfy {min} ≤ min_pu < max_pu ≤ {max} | Invalid limit values |
| `INVALID_PHASE` | Invalid phase: {phase}. Must be "1", "2", "3", or null | Invalid phase filter |

---

## 4. analyze_capacity

Analyze maximum DER hosting capacity at a specific bus.

### Function Signature

```python
def analyze_capacity(
    bus_id: str,
    der_type: str = "solar",
    increment_kw: float = 100,
    max_capacity_kw: float = 10000,
    constraints: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `bus_id` | `string` | Yes | - | Bus identifier where DER will be connected |
| `der_type` | `string` | No | `"solar"` | DER type: `"solar"`, `"battery"`, `"wind"` |
| `increment_kw` | `float` | No | `100` | Capacity increment for each iteration (kW) |
| `max_capacity_kw` | `float` | No | `10000` | Maximum capacity to test (kW) |
| `constraints` | `dict` | No | `{}` | Constraint limits (see Constraints section) |

#### Constraints Structure

```python
{
  "min_voltage_pu": float,     # Minimum voltage limit (default: 0.95)
  "max_voltage_pu": float,     # Maximum voltage limit (default: 1.05)
  "max_line_loading_pct": float  # Max line loading percent (default: 100.0)
}
```

### Return Format

```typescript
{
  success: boolean,
  data: {
    bus_id: string,
    der_type: string,
    max_capacity_kw: number,     // Maximum capacity before violation
    limiting_constraint: string, // "max_voltage", "min_voltage", "max_loading", or "none"
    capacity_curve: Array<{
      capacity_kw: number,
      min_voltage_pu: number,
      max_voltage_pu: number,
      max_loading_pct: number,
      losses_kw: number,
      violation?: string         // Present if constraint violated
    }>,
    violation_details?: {        // Present if capacity limited
      constraint: string,
      limit: number,
      value: number,
      bus: string
    }
  },
  metadata: {
    timestamp: string,
    execution_time_ms: number,
    iterations: number           // Number of capacity iterations tested
  },
  errors: null
}
```

### Example Request

```json
{
  "tool": "analyze_capacity",
  "parameters": {
    "bus_id": "675",
    "der_type": "solar",
    "increment_kw": 500,
    "max_capacity_kw": 5000,
    "constraints": {
      "min_voltage_pu": 0.95,
      "max_voltage_pu": 1.05,
      "max_line_loading_pct": 100.0
    }
  }
}
```

### Example Response (Success)

```json
{
  "success": true,
  "data": {
    "bus_id": "675",
    "der_type": "solar",
    "max_capacity_kw": 2500,
    "limiting_constraint": "max_voltage",
    "capacity_curve": [
      {
        "capacity_kw": 0,
        "min_voltage_pu": 0.9542,
        "max_voltage_pu": 1.0500,
        "max_loading_pct": 65.2,
        "losses_kw": 116.2
      },
      {
        "capacity_kw": 500,
        "min_voltage_pu": 0.9654,
        "max_voltage_pu": 1.0498,
        "max_loading_pct": 62.1,
        "losses_kw": 108.5
      },
      {
        "capacity_kw": 1000,
        "min_voltage_pu": 0.9766,
        "max_voltage_pu": 1.0496,
        "max_loading_pct": 58.9,
        "losses_kw": 98.3
      },
      {
        "capacity_kw": 1500,
        "min_voltage_pu": 0.9878,
        "max_voltage_pu": 1.0494,
        "max_loading_pct": 55.4,
        "losses_kw": 85.7
      },
      {
        "capacity_kw": 2000,
        "min_voltage_pu": 0.9990,
        "max_voltage_pu": 1.0492,
        "max_loading_pct": 51.2,
        "losses_kw": 70.1
      },
      {
        "capacity_kw": 2500,
        "min_voltage_pu": 1.0102,
        "max_voltage_pu": 1.0490,
        "max_loading_pct": 46.5,
        "losses_kw": 51.2
      },
      {
        "capacity_kw": 3000,
        "min_voltage_pu": 1.0214,
        "max_voltage_pu": 1.0488,
        "max_loading_pct": 41.3,
        "losses_kw": 29.1,
        "violation": "max_voltage"
      }
    ],
    "violation_details": {
      "constraint": "max_voltage",
      "limit": 1.05,
      "value": 1.0214,
      "bus": "675"
    }
  },
  "metadata": {
    "timestamp": "2025-10-14T11:00:00.000Z",
    "execution_time_ms": 3420,
    "iterations": 7
  },
  "errors": null
}
```

### Error Codes

| Code | Message | Description |
|------|---------|-------------|
| `NO_CIRCUIT_LOADED` | No circuit loaded. Load a feeder first. | No feeder loaded |
| `INVALID_BUS` | Bus '{bus_id}' not found in circuit | Bus doesn't exist |
| `INVALID_DER_TYPE` | Invalid DER type: {type}. Valid: solar, battery, wind | Unsupported DER type |
| `INVALID_INCREMENT` | Increment must be positive, got {value} | Invalid increment value |
| `ANALYSIS_ERROR` | Error during capacity analysis: {details} | Analysis failure |

---

## 5. optimize_der

Optimize DER placement to achieve a specified objective.

### Function Signature

```python
def optimize_der(
    der_type: str,
    capacity_kw: float,
    battery_kwh: Optional[float] = None,
    objective: str = "minimize_losses",
    candidate_buses: Optional[list] = None,
    constraints: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `der_type` | `string` | Yes | - | DER type: `"solar"`, `"battery"`, `"solar_battery"`, `"ev_charger"`, `"wind"` |
| `capacity_kw` | `float` | Yes | - | DER capacity in kW |
| `battery_kwh` | `float` | No | `null` | Battery energy capacity in kWh (required for battery types) |
| `objective` | `string` | No | `"minimize_losses"` | Optimization objective (see Objectives) |
| `candidate_buses` | `string[]` | No | `null` | List of bus IDs to evaluate (null = all buses, max 20) |
| `constraints` | `dict` | No | `{}` | Constraint limits |

#### Optimization Objectives

| Objective | Description |
|-----------|-------------|
| `"minimize_losses"` | Minimize total system real power losses |
| `"maximize_capacity"` | Maximize DER capacity before constraint violations |
| `"minimize_violations"` | Minimize number of voltage violations |

#### Constraints Structure

```python
{
  "min_voltage_pu": float,     # Minimum voltage limit (default: 0.95)
  "max_voltage_pu": float,     # Maximum voltage limit (default: 1.05)
  "max_candidates": int        # Maximum buses to evaluate (default: 20)
}
```

### Return Format

```typescript
{
  success: boolean,
  data: {
    optimal_bus: string,         // Best bus for DER placement
    der_type: string,
    capacity_kw: number,
    objective: string,
    baseline: {                  // System without DER
      total_losses_kw: number,
      min_voltage_pu: number,
      max_voltage_pu: number,
      voltage_violations: number
    },
    optimal_case: {              // System with DER at optimal bus
      total_losses_kw: number,
      min_voltage_pu: number,
      max_voltage_pu: number,
      voltage_violations: number
    },
    improvement_metrics: {
      loss_reduction_kw: number,
      loss_reduction_pct: number,
      voltage_improvement_pu: number,
      violations_fixed: number
    },
    comparison_table: Array<{    // Ranked results for all candidates
      bus: string,
      losses_kw: number,
      min_voltage: number,
      violations: number,
      rank: number
    }>,
    candidates_evaluated: number
  },
  metadata: {
    timestamp: string,
    execution_time_ms: number,
    power_flow_runs: number      // Number of power flows executed
  },
  errors: null
}
```

### Example Request

```json
{
  "tool": "optimize_der",
  "parameters": {
    "der_type": "solar",
    "capacity_kw": 2000,
    "battery_kwh": null,
    "objective": "minimize_losses",
    "candidate_buses": null,
    "constraints": {
      "min_voltage_pu": 0.95,
      "max_voltage_pu": 1.05,
      "max_candidates": 20
    }
  }
}
```

### Example Response (Success)

```json
{
  "success": true,
  "data": {
    "optimal_bus": "675",
    "der_type": "solar",
    "capacity_kw": 2000,
    "objective": "minimize_losses",
    "baseline": {
      "total_losses_kw": 116.2,
      "min_voltage_pu": 0.9542,
      "max_voltage_pu": 1.0500,
      "voltage_violations": 3
    },
    "optimal_case": {
      "total_losses_kw": 78.5,
      "min_voltage_pu": 0.9712,
      "max_voltage_pu": 1.0498,
      "voltage_violations": 0
    },
    "improvement_metrics": {
      "loss_reduction_kw": 37.7,
      "loss_reduction_pct": 32.4,
      "voltage_improvement_pu": 0.0170,
      "violations_fixed": 3
    },
    "comparison_table": [
      {
        "bus": "675",
        "losses_kw": 78.5,
        "min_voltage": 0.9712,
        "violations": 0,
        "rank": 1
      },
      {
        "bus": "634",
        "losses_kw": 82.3,
        "min_voltage": 0.9698,
        "violations": 0,
        "rank": 2
      },
      {
        "bus": "671",
        "losses_kw": 85.1,
        "min_voltage": 0.9680,
        "violations": 1,
        "rank": 3
      }
    ],
    "candidates_evaluated": 13
  },
  "metadata": {
    "timestamp": "2025-10-14T11:15:00.000Z",
    "execution_time_ms": 5230,
    "power_flow_runs": 14
  },
  "errors": null
}
```

### Error Codes

| Code | Message | Description |
|------|---------|-------------|
| `NO_CIRCUIT_LOADED` | No circuit loaded. Load a feeder first. | No feeder loaded |
| `INVALID_DER_TYPE` | Invalid DER type: {type} | Unsupported DER type |
| `INVALID_CAPACITY` | Capacity must be positive, got {value} | Invalid capacity value |
| `INVALID_OBJECTIVE` | Invalid objective: {objective} | Unsupported objective |
| `NO_CANDIDATES` | No valid candidate buses found | All buses invalid/failed |
| `OPTIMIZATION_ERROR` | Optimization failed: {details} | Optimization failure |

---

## 6. run_timeseries

Run time-series power flow simulation with load and generation profiles.

### Function Signature

```python
def run_timeseries(
    load_profile: Union[str, dict],
    generation_profile: Optional[Union[str, dict]] = None,
    duration_hours: int = 24,
    timestep_minutes: int = 60,
    output_variables: Optional[list] = None
) -> Dict[str, Any]
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `load_profile` | `string` or `dict` | Yes | - | Load profile name or custom profile (see Profile Format) |
| `generation_profile` | `string` or `dict` | No | `null` | Generation profile name or custom profile |
| `duration_hours` | `int` | No | `24` | Simulation duration in hours |
| `timestep_minutes` | `int` | No | `60` | Time step resolution in minutes |
| `output_variables` | `string[]` | No | `["voltages", "losses"]` | Variables to track |

#### Profile Format

**String (named profile):**
```python
"residential_summer"
```

**Dictionary (custom profile):**
```python
{
  "name": "custom_profile",
  "multipliers": [0.4, 0.35, 0.3, ...]  # One value per timestep
}
```

#### Output Variables

| Variable | Description | Data Returned |
|----------|-------------|---------------|
| `"voltages"` | Bus voltages | Min/max/avg voltage per timestep |
| `"losses"` | System losses | Real and reactive losses per timestep |
| `"loadings"` | Line loading | Maximum line loading per timestep |
| `"powers"` | Bus powers | Real and reactive power per bus |

### Return Format

```typescript
{
  success: boolean,
  data: {
    timesteps: Array<{
      hour: number,
      time: string,              // HH:MM format
      converged: boolean,
      min_voltage_pu: number,
      max_voltage_pu: number,
      avg_voltage_pu: number,
      total_losses_kw: number,
      total_load_kw: number,
      max_line_loading_pct: number
    }>,
    summary: {
      num_timesteps: number,
      convergence_rate_pct: number,  // % of timesteps that converged
      min_voltage_pu: number,        // Worst voltage across all timesteps
      max_voltage_pu: number,        // Highest voltage across all timesteps
      avg_losses_kw: number,
      peak_load_kw: number,
      peak_load_hour: number,
      total_energy_delivered_kwh: number,
      total_energy_losses_kwh: number,
      loss_percentage: number,
      voltage_violation_hours: number
    }
  },
  metadata: {
    timestamp: string,
    execution_time_ms: number,
    load_profile: string,
    generation_profile: string | null
  },
  errors: null
}
```

### Example Request

```json
{
  "tool": "run_timeseries",
  "parameters": {
    "load_profile": {
      "name": "custom_residential",
      "multipliers": [0.4, 0.35, 0.3, 0.3, 0.35, 0.5, 0.7, 0.85, 0.9, 0.85, 0.8, 0.75, 0.7, 0.75, 0.8, 0.85, 0.95, 1.0, 0.95, 0.85, 0.75, 0.65, 0.55, 0.45]
    },
    "generation_profile": {
      "name": "solar_clear_day",
      "multipliers": [0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.3, 0.6, 0.8, 0.95, 1.0, 0.95, 0.9, 0.8, 0.6, 0.3, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    },
    "duration_hours": 24,
    "timestep_minutes": 60,
    "output_variables": ["voltages", "losses", "loadings"]
  }
}
```

### Example Response (Success)

```json
{
  "success": true,
  "data": {
    "timesteps": [
      {
        "hour": 0,
        "time": "00:00",
        "converged": true,
        "min_voltage_pu": 0.9623,
        "max_voltage_pu": 1.0500,
        "avg_voltage_pu": 0.9912,
        "total_losses_kw": 85.3,
        "total_load_kw": 2845.6,
        "max_line_loading_pct": 52.1
      },
      {
        "hour": 1,
        "time": "01:00",
        "converged": true,
        "min_voltage_pu": 0.9645,
        "max_voltage_pu": 1.0500,
        "avg_voltage_pu": 0.9925,
        "total_losses_kw": 76.8,
        "total_load_kw": 2567.3,
        "max_line_loading_pct": 48.5
      }
    ],
    "summary": {
      "num_timesteps": 24,
      "convergence_rate_pct": 100.0,
      "min_voltage_pu": 0.9542,
      "max_voltage_pu": 1.0512,
      "avg_losses_kw": 98.5,
      "peak_load_kw": 3842.1,
      "peak_load_hour": 18,
      "total_energy_delivered_kwh": 78234.5,
      "total_energy_losses_kwh": 2364.0,
      "loss_percentage": 3.02,
      "voltage_violation_hours": 2
    }
  },
  "metadata": {
    "timestamp": "2025-10-14T11:30:00.000Z",
    "execution_time_ms": 8920,
    "load_profile": "custom_residential",
    "generation_profile": "solar_clear_day"
  },
  "errors": null
}
```

### Error Codes

| Code | Message | Description |
|------|---------|-------------|
| `NO_CIRCUIT_LOADED` | No circuit loaded. Load a feeder first. | No feeder loaded |
| `INVALID_PROFILE` | Invalid profile format: {details} | Malformed profile |
| `PROFILE_LENGTH_MISMATCH` | Profile length ({n}) doesn't match timesteps ({m}) | Profile too short/long |
| `INVALID_DURATION` | Duration must be positive, got {value} | Invalid duration |
| `INVALID_TIMESTEP` | Timestep must be between 1 and 60 minutes | Invalid timestep |
| `SIMULATION_ERROR` | Time-series simulation failed: {details} | Simulation failure |

---

## 7. create_visualization

Generate professional visualizations for power system analysis results.

### Function Signature

```python
def create_visualization(
    plot_type: str,
    data_source: str = "circuit",
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `plot_type` | `string` | Yes | - | Type of visualization (see Plot Types) |
| `data_source` | `string` | No | `"circuit"` | Data source to visualize (see Data Sources) |
| `options` | `dict` | No | `{}` | Plot customization options |

#### Plot Types

| Plot Type | Description |
|-----------|-------------|
| `"voltage_profile"` | Bar chart of bus voltages with violation highlighting |
| `"network_diagram"` | Network topology diagram with voltage-colored nodes |
| `"timeseries"` | Multi-panel line plots for time-varying data |
| `"capacity_curve"` | Scatter plot for DER hosting capacity analysis |
| `"harmonics_spectrum"` | Bar chart of harmonic voltage magnitudes |

#### Data Sources

| Source | Compatible Plot Types |
|--------|----------------------|
| `"circuit"` | voltage_profile, network_diagram |
| `"last_power_flow"` | voltage_profile, network_diagram |
| `"last_timeseries"` | timeseries |
| `"last_capacity"` | capacity_curve |
| `"last_harmonics"` | harmonics_spectrum |

#### Options Structure

```python
{
  "save_path": str,            # File path to save (if null, returns base64)
  "figsize": tuple,            # Figure size (width, height) in inches
  "dpi": int,                  # Resolution in dots per inch
  "title": str,                # Custom plot title
  "show_violations": bool,     # Highlight voltage violations (default: true)
  "bus_filter": list           # Specific buses to include (null = all)
}
```

### Return Format

```typescript
{
  success: boolean,
  data: {
    plot_type: string,
    data_source: string,
    file_path: string | null,    // Path if saved, null if base64
    image_base64: string | null, // Base64-encoded PNG if not saved
    dimensions: {
      width_inches: number,
      height_inches: number,
      dpi: number
    },
    content: {                   // Plot-specific metadata
      num_buses?: number,
      num_violations?: number,
      voltage_range?: number[],
      timesteps?: number
    }
  },
  metadata: {
    timestamp: string,
    execution_time_ms: number
  },
  errors: null
}
```

### Example Request

```json
{
  "tool": "create_visualization",
  "parameters": {
    "plot_type": "voltage_profile",
    "data_source": "circuit",
    "options": {
      "save_path": null,
      "figsize": [14, 6],
      "dpi": 100,
      "title": "IEEE13 Voltage Profile Analysis",
      "show_violations": true,
      "bus_filter": null
    }
  }
}
```

### Example Response (Success - Base64)

```json
{
  "success": true,
  "data": {
    "plot_type": "voltage_profile",
    "data_source": "circuit",
    "file_path": null,
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAABLAAAASwCAYAA...",
    "dimensions": {
      "width_inches": 14,
      "height_inches": 6,
      "dpi": 100
    },
    "content": {
      "num_buses": 13,
      "num_violations": 3,
      "voltage_range": [0.9542, 1.0500]
    }
  },
  "metadata": {
    "timestamp": "2025-10-14T12:00:00.000Z",
    "execution_time_ms": 234
  },
  "errors": null
}
```

### Example Response (Success - Saved File)

```json
{
  "success": true,
  "data": {
    "plot_type": "voltage_profile",
    "data_source": "circuit",
    "file_path": "/path/to/voltage_profile.png",
    "image_base64": null,
    "dimensions": {
      "width_inches": 14,
      "height_inches": 6,
      "dpi": 300
    },
    "content": {
      "num_buses": 13,
      "num_violations": 3,
      "voltage_range": [0.9542, 1.0500]
    }
  },
  "metadata": {
    "timestamp": "2025-10-14T12:00:00.000Z",
    "execution_time_ms": 412
  },
  "errors": null
}
```

### Error Codes

| Code | Message | Description |
|------|---------|-------------|
| `NO_DATA` | No data available for plot type: {type} | Data source empty |
| `INVALID_PLOT_TYPE` | Invalid plot type: {type} | Unsupported plot type |
| `INVALID_DATA_SOURCE` | Invalid data source: {source} | Unsupported data source |
| `INCOMPATIBLE_SOURCE` | Data source '{source}' not compatible with plot type '{type}' | Mismatched source/type |
| `SAVE_ERROR` | Error saving file to {path}: {details} | File save failure |
| `RENDER_ERROR` | Error rendering visualization: {details} | Rendering failure |

---

## Utility Functions

### Validators

Module: `opendss_mcp.utils.validators`

#### validate_bus_id

```python
def validate_bus_id(bus_id: str, dss_circuit: DSSCircuit) -> None
```

Validate that a bus ID exists in the current circuit.

**Parameters:**
- `bus_id` (str): The bus ID to validate
- `dss_circuit` (DSSCircuit): Instance of DSSCircuit to check against

**Raises:**
- `ValueError`: If the bus ID is not found in the circuit
- `RuntimeError`: If there's an error accessing circuit buses

**Example:**
```python
from opendss_mcp.utils.validators import validate_bus_id
from opendss_mcp.utils.dss_wrapper import DSSCircuit

circuit = DSSCircuit()
validate_bus_id("675", circuit)  # Raises ValueError if not found
```

---

#### validate_positive_float

```python
def validate_positive_float(value: float, name: str) -> None
```

Validate that a numeric value is positive.

**Parameters:**
- `value` (float): The value to validate
- `name` (str): The name of the parameter (used in error message)

**Raises:**
- `ValueError`: If the value is not a positive number

**Example:**
```python
from opendss_mcp.utils.validators import validate_positive_float

validate_positive_float(100.0, "capacity_kw")  # OK
validate_positive_float(-50.0, "capacity_kw")  # Raises ValueError
validate_positive_float(0.0, "capacity_kw")    # Raises ValueError
```

---

#### validate_voltage_limits

```python
def validate_voltage_limits(min_pu: float, max_pu: float) -> None
```

Validate voltage limits are within acceptable range and min < max.

**Parameters:**
- `min_pu` (float): Minimum voltage in per-unit
- `max_pu` (float): Maximum voltage in per-unit

**Raises:**
- `ValueError`: If voltage limits are outside valid range (0.8-1.2 pu) or min >= max

**Constants:**
- `MIN_VOLTAGE_PU = 0.8`: Absolute minimum allowed
- `MAX_VOLTAGE_PU = 1.2`: Absolute maximum allowed

**Example:**
```python
from opendss_mcp.utils.validators import validate_voltage_limits

validate_voltage_limits(0.95, 1.05)  # OK
validate_voltage_limits(1.05, 0.95)  # Raises ValueError (min >= max)
validate_voltage_limits(0.5, 1.05)   # Raises ValueError (below 0.8)
```

---

#### validate_feeder_id

```python
def validate_feeder_id(feeder_id: str) -> None
```

Validate that the feeder ID is one of the supported IEEE test feeders.

**Parameters:**
- `feeder_id` (str): The feeder ID to validate

**Raises:**
- `ValueError`: If the feeder ID is not in the list of supported feeders

**Constants:**
- `VALID_FEEDER_IDS = ["IEEE13", "IEEE34", "IEEE123"]`

**Example:**
```python
from opendss_mcp.utils.validators import validate_feeder_id

validate_feeder_id("IEEE13")   # OK
validate_feeder_id("IEEE999")  # Raises ValueError
```

---

### Formatters

Module: `opendss_mcp.utils.formatters`

#### format_success_response

```python
def format_success_response(
    data: Union[Dict[str, Any], List[Any]],
    metadata: Optional[Dict[str, Any]] = None
) -> SuccessResponse
```

Format a successful API response.

**Parameters:**
- `data` (dict or list): The main response data
- `metadata` (dict, optional): Additional metadata

**Returns:**
- `SuccessResponse`: Formatted success response with standard structure

**Example:**
```python
from opendss_mcp.utils.formatters import format_success_response

data = {"voltage": 1.02, "bus": "675"}
metadata = {"timestamp": "2025-10-14T10:00:00Z"}
response = format_success_response(data, metadata)
# {
#   "success": True,
#   "data": {"voltage": 1.02, "bus": "675"},
#   "metadata": {"timestamp": "2025-10-14T10:00:00Z"},
#   "errors": None
# }
```

---

#### format_error_response

```python
def format_error_response(errors: Union[str, List[str]]) -> ErrorResponse
```

Format an error response.

**Parameters:**
- `errors` (str or list): Single error message or list of error messages

**Returns:**
- `ErrorResponse`: Formatted error response with standard structure

**Example:**
```python
from opendss_mcp.utils.formatters import format_error_response

response = format_error_response("Bus not found")
# {
#   "success": False,
#   "data": None,
#   "metadata": None,
#   "errors": ["Bus not found"]
# }

response = format_error_response(["Error 1", "Error 2"])
# {
#   "success": False,
#   "data": None,
#   "metadata": None,
#   "errors": ["Error 1", "Error 2"]
# }
```

---

#### format_voltage_results

```python
def format_voltage_results(voltages: Dict[str, float]) -> Dict[str, Any]
```

Calculate and format voltage statistics.

**Parameters:**
- `voltages` (dict): Dictionary mapping bus names to voltage magnitudes (p.u.)

**Returns:**
- `dict`: Dictionary containing:
  - `min` (float): Minimum voltage
  - `max` (float): Maximum voltage
  - `avg` (float): Average voltage
  - `min_bus` (str): Bus with minimum voltage
  - `max_bus` (str): Bus with maximum voltage

**Example:**
```python
from opendss_mcp.utils.formatters import format_voltage_results

voltages = {"650": 1.05, "671": 0.98, "675": 0.95}
stats = format_voltage_results(voltages)
# {
#   "min": 0.95,
#   "max": 1.05,
#   "avg": 0.9933,
#   "min_bus": "675",
#   "max_bus": "650"
# }
```

---

#### format_line_flow_results

```python
def format_line_flow_results(flows: Dict[str, Dict[str, float]]) -> Dict[str, Any]
```

Calculate and format line flow statistics.

**Parameters:**
- `flows` (dict): Dictionary mapping line names to flow information. Each flow must contain:
  - `P` (float): Real power flow (kW)
  - `Q` (float): Reactive power flow (kvar)
  - `loading` (float): Line loading percentage

**Returns:**
- `dict`: Dictionary containing:
  - `max_loading` (float): Maximum line loading percentage
  - `max_loading_line` (str): Line with maximum loading
  - `total_p` (float): Total real power (kW)
  - `total_q` (float): Total reactive power (kvar)
  - `line_count` (int): Number of lines

**Example:**
```python
from opendss_mcp.utils.formatters import format_line_flow_results

flows = {
    "Line1": {"P": 100, "Q": 50, "loading": 65.2},
    "Line2": {"P": 200, "Q": 75, "loading": 82.1}
}
stats = format_line_flow_results(flows)
# {
#   "max_loading": 82.1,
#   "max_loading_line": "Line2",
#   "total_p": 300.0,
#   "total_q": 125.0,
#   "line_count": 2
# }
```

---

### Harmonics Utilities

Module: `opendss_mcp.utils.harmonics`

#### run_frequency_scan

```python
def run_frequency_scan(orders: list[int] | None = None) -> dict[str, Any]
```

Run frequency scan to analyze harmonic content in the circuit.

**Parameters:**
- `orders` (list, optional): List of harmonic orders to scan (e.g., `[3, 5, 7, 9, 11, 13]`). Default: `[3, 5, 7, 9, 11, 13]`

**Returns:**
- `dict`: Dictionary containing:
  - `success` (bool): Whether scan was successful
  - `harmonic_data` (dict): Mapping of harmonic order to results
  - `fundamental_frequency_hz` (float): Fundamental frequency (typically 60 Hz)
  - `errors` (list): List of error messages

**Example:**
```python
from opendss_mcp.utils.harmonics import run_frequency_scan

result = run_frequency_scan([3, 5, 7])
if result['success']:
    for order, data in result['harmonic_data'].items():
        print(f"Order {order}: {data['frequency_hz']} Hz, Converged: {data['converged']}")
```

---

#### calculate_thd

```python
def calculate_thd(harmonics: dict[int, float]) -> float
```

Calculate Total Harmonic Distortion (THD) from harmonic magnitudes.

**Formula:**
```
THD = sqrt(sum(H_n^2 for n > 1)) / H_1 * 100
```

**Parameters:**
- `harmonics` (dict): Dictionary mapping harmonic order to magnitude. Must include order 1 (fundamental).

**Returns:**
- `float`: THD percentage. Returns 0.0 if fundamental is missing or zero.

**Example:**
```python
from opendss_mcp.utils.harmonics import calculate_thd

harmonics = {1: 120.0, 3: 10.0, 5: 8.0, 7: 5.0}
thd = calculate_thd(harmonics)
print(f"THD: {thd:.2f}%")  # THD: 11.18%
```

---

#### get_harmonic_voltages

```python
def get_harmonic_voltages(bus_id: str, orders: list[int] | None = None) -> dict[str, Any]
```

Get voltage magnitudes at each harmonic order for a specific bus.

**Parameters:**
- `bus_id` (str): Identifier of the bus to analyze
- `orders` (list, optional): List of harmonic orders. Default: `[1, 3, 5, 7, 9, 11, 13]`

**Returns:**
- `dict`: Dictionary containing:
  - `success` (bool): Operation success status
  - `bus_id` (str): The bus identifier
  - `harmonic_voltages` (dict): Mapping of order to voltage data
  - `thd_percent` (float): Total harmonic distortion percentage
  - `fundamental_voltage_pu` (float): Fundamental voltage magnitude
  - `errors` (list): List of error messages

**Example:**
```python
from opendss_mcp.utils.harmonics import get_harmonic_voltages

result = get_harmonic_voltages("675", [1, 3, 5, 7])
if result['success']:
    print(f"Bus {result['bus_id']}, THD: {result['thd_percent']:.2f}%")
    for order, data in result['harmonic_voltages'].items():
        print(f"  Order {order}: {data['avg_voltage_pu']:.4f} pu")
```

---

#### get_harmonic_currents

```python
def get_harmonic_currents(line_id: str, orders: list[int] | None = None) -> dict[str, Any]
```

Get current magnitudes at each harmonic order for a specific line.

**Parameters:**
- `line_id` (str): Identifier of the line (with or without "Line." prefix)
- `orders` (list, optional): List of harmonic orders. Default: `[1, 3, 5, 7, 9, 11, 13]`

**Returns:**
- `dict`: Dictionary containing:
  - `success` (bool): Operation success status
  - `line_id` (str): The line identifier
  - `harmonic_currents` (dict): Mapping of order to current data
  - `thd_percent` (float): Total harmonic distortion percentage
  - `fundamental_current_amps` (float): Fundamental current magnitude
  - `errors` (list): List of error messages

**Example:**
```python
from opendss_mcp.utils.harmonics import get_harmonic_currents

result = get_harmonic_currents("Line.650632", [1, 3, 5, 7])
if result['success']:
    print(f"Line {result['line_id']}, THD: {result['thd_percent']:.2f}%")
    for order, data in result['harmonic_currents'].items():
        print(f"  Order {order}: {data['max_current_amps']:.2f} A")
```

---

### Inverter Control Utilities

Module: `opendss_mcp.utils.inverter_control`

#### load_curve

```python
def load_curve(curve_name: str) -> list[tuple[float, float]]
```

Load control curve points from a JSON file.

**Parameters:**
- `curve_name` (str): Name of standard curve (`"IEEE1547"`, `"RULE21"`) or path to custom JSON file

**Returns:**
- `list`: List of (x, y) tuples representing curve points

**Raises:**
- `FileNotFoundError`: If the specified curve file doesn't exist
- `ValueError`: If the JSON file is invalid or missing required fields
- `KeyError`: If the curve name is not recognized

**Standard Curves:**
- `"IEEE1547"`: IEEE 1547-2018 Category B volt-var curve
- `"RULE21"`: California Rule 21 volt-var curve

**Example:**
```python
from opendss_mcp.utils.inverter_control import load_curve

# Load standard curve
points = load_curve("IEEE1547")
print(points)  # [(0.92, 0.44), (0.98, 0.0), (1.02, 0.0), (1.08, -0.44)]

# Load custom curve
points = load_curve("path/to/custom_curve.json")
```

---

#### configure_volt_var_control

```python
def configure_volt_var_control(
    pv_name: str,
    curve_points: list[tuple[float, float]],
    response_time: float = 10.0,
    curve_name: str | None = None
) -> None
```

Configure volt-var control for a PV system or inverter in OpenDSS.

**Parameters:**
- `pv_name` (str): Name of the PVSystem element (without "PVSystem." prefix)
- `curve_points` (list): List of (voltage_pu, var_pu) tuples defining the curve
- `response_time` (float, optional): Response time in seconds. Default: 10.0
- `curve_name` (str, optional): Name for the XYCurve. Default: auto-generated

**Raises:**
- `ValueError`: If curve has fewer than 2 points
- `RuntimeError`: If configuration fails

**Example:**
```python
from opendss_mcp.utils.inverter_control import load_curve, configure_volt_var_control

# Load and apply IEEE 1547 curve
curve = load_curve("IEEE1547")
configure_volt_var_control("PV_675", curve, response_time=5.0)

# Custom curve
custom_curve = [(0.95, 0.44), (0.98, 0.0), (1.02, 0.0), (1.05, -0.44)]
configure_volt_var_control("PV_611", custom_curve)
```

---

#### configure_volt_watt_control

```python
def configure_volt_watt_control(
    pv_name: str,
    curve_points: list[tuple[float, float]],
    curve_name: str | None = None
) -> None
```

Configure volt-watt control for a PV system or inverter in OpenDSS.

**Parameters:**
- `pv_name` (str): Name of the PVSystem element (without "PVSystem." prefix)
- `curve_points` (list): List of (voltage_pu, watt_pu) tuples defining the curve
- `curve_name` (str, optional): Name for the XYCurve. Default: auto-generated

**Raises:**
- `ValueError`: If curve has fewer than 2 points
- `RuntimeError`: If configuration fails

**Example:**
```python
from opendss_mcp.utils.inverter_control import configure_volt_watt_control

# Typical volt-watt curve: curtail above 1.06 pu
vw_curve = [
    (0.00, 1.00),  # Normal operation
    (1.06, 1.00),  # Start curtailment
    (1.10, 0.20)   # 80% curtailment at 1.10 pu
]
configure_volt_watt_control("PV_675", vw_curve)
```

---

#### get_inverter_status

```python
def get_inverter_status(pv_name: str) -> dict[str, Any]
```

Get current status of a PVSystem inverter including control outputs.

**Parameters:**
- `pv_name` (str): Name of the PVSystem element (without "PVSystem." prefix)

**Returns:**
- `dict`: Dictionary containing:
  - `success` (bool): Whether status was retrieved
  - `pv_name` (str): The PVSystem name
  - `kw` (float): Real power output in kW
  - `kvar` (float): Reactive power output in kvar
  - `kva` (float): Apparent power in kVA
  - `pf` (float): Power factor
  - `voltage_pu` (float): Terminal voltage in per-unit
  - `errors` (list): List of error messages

**Example:**
```python
from opendss_mcp.utils.inverter_control import get_inverter_status

status = get_inverter_status("PV_675")
if status["success"]:
    print(f"PV Output: {status['kw']:.2f} kW, {status['kvar']:.2f} kvar")
    print(f"Voltage: {status['voltage_pu']:.4f} pu, PF: {status['pf']:.3f}")
```

---

#### list_available_curves

```python
def list_available_curves() -> list[dict[str, str]]
```

List all available standard control curves.

**Returns:**
- `list`: List of dictionaries containing:
  - `name` (str): Curve name (for use with `load_curve`)
  - `file` (str): JSON filename
  - `description` (str): Curve description
  - `type` (str): Control type (volt-var, volt-watt, etc.)

**Example:**
```python
from opendss_mcp.utils.inverter_control import list_available_curves

curves = list_available_curves()
for curve in curves:
    print(f"{curve['name']}: {curve['description']}")
# IEEE1547: IEEE 1547-2018 Category B volt-var curve
# RULE21: California Rule 21 volt-var curve
```

---

## Error Codes

### Standard Error Response Format

All errors follow this structure:

```json
{
  "success": false,
  "data": null,
  "metadata": null,
  "errors": ["Error message 1", "Error message 2"]
}
```

### Error Code Categories

#### Circuit State Errors

| Code | Message | HTTP Equivalent | Description |
|------|---------|-----------------|-------------|
| `NO_CIRCUIT_LOADED` | No circuit loaded. Load a feeder first. | 400 Bad Request | Operation requires loaded circuit |
| `NO_SOLUTION` | No power flow solution available. Run power flow first. | 400 Bad Request | Operation requires solved circuit |
| `CIRCUIT_STATE_ERROR` | Circuit state inconsistent: {details} | 500 Internal Server Error | Circuit in invalid state |

#### Validation Errors

| Code | Message | HTTP Equivalent | Description |
|------|---------|-----------------|-------------|
| `INVALID_FEEDER_ID` | Unsupported feeder ID: '{id}' | 400 Bad Request | Invalid feeder identifier |
| `INVALID_BUS` | Bus '{bus_id}' not found in circuit | 404 Not Found | Bus doesn't exist |
| `INVALID_LINE` | Line '{line_id}' not found in circuit | 404 Not Found | Line doesn't exist |
| `INVALID_PARAMETER` | Invalid parameter '{param}': {details} | 400 Bad Request | Parameter validation failed |
| `INVALID_LIMITS` | Voltage limits must satisfy {constraints} | 400 Bad Request | Invalid voltage limits |
| `INVALID_CAPACITY` | Capacity must be positive, got {value} | 400 Bad Request | Invalid capacity value |
| `INVALID_INCREMENT` | Increment must be positive, got {value} | 400 Bad Request | Invalid increment value |
| `INVALID_DER_TYPE` | Invalid DER type: {type} | 400 Bad Request | Unsupported DER type |
| `INVALID_OBJECTIVE` | Invalid objective: {objective} | 400 Bad Request | Unsupported objective |
| `INVALID_PHASE` | Invalid phase: {phase}. Must be "1", "2", "3", or null | 400 Bad Request | Invalid phase filter |

#### OpenDSS Errors

| Code | Message | HTTP Equivalent | Description |
|------|---------|-----------------|-------------|
| `DSS_FILE_NOT_FOUND` | DSS file not found at path: '{path}' | 404 Not Found | DSS file missing |
| `DSS_COMPILE_ERROR` | Failed to compile DSS file: {details} | 500 Internal Server Error | OpenDSS compilation failure |
| `CONVERGENCE_FAILURE` | Power flow did not converge after {n} iterations | 500 Internal Server Error | Solution didn't converge |
| `SOLUTION_ERROR` | OpenDSS solution error: {details} | 500 Internal Server Error | OpenDSS internal error |

#### Analysis Errors

| Code | Message | HTTP Equivalent | Description |
|------|---------|-----------------|-------------|
| `ANALYSIS_ERROR` | Error during capacity analysis: {details} | 500 Internal Server Error | Capacity analysis failed |
| `OPTIMIZATION_ERROR` | Optimization failed: {details} | 500 Internal Server Error | Optimization failure |
| `SIMULATION_ERROR` | Time-series simulation failed: {details} | 500 Internal Server Error | Time-series failure |
| `NO_CANDIDATES` | No valid candidate buses found | 400 Bad Request | All buses invalid/failed |

#### Visualization Errors

| Code | Message | HTTP Equivalent | Description |
|------|---------|-----------------|-------------|
| `NO_DATA` | No data available for plot type: {type} | 400 Bad Request | Data source empty |
| `INVALID_PLOT_TYPE` | Invalid plot type: {type} | 400 Bad Request | Unsupported plot type |
| `INVALID_DATA_SOURCE` | Invalid data source: {source} | 400 Bad Request | Unsupported data source |
| `INCOMPATIBLE_SOURCE` | Data source '{source}' not compatible with plot type '{type}' | 400 Bad Request | Mismatched source/type |
| `SAVE_ERROR` | Error saving file to {path}: {details} | 500 Internal Server Error | File save failure |
| `RENDER_ERROR` | Error rendering visualization: {details} | 500 Internal Server Error | Rendering failure |

#### File and Profile Errors

| Code | Message | HTTP Equivalent | Description |
|------|---------|-----------------|-------------|
| `FILE_NOT_FOUND` | File not found: {path} | 404 Not Found | File doesn't exist |
| `INVALID_PROFILE` | Invalid profile format: {details} | 400 Bad Request | Malformed profile |
| `PROFILE_LENGTH_MISMATCH` | Profile length ({n}) doesn't match timesteps ({m}) | 400 Bad Request | Profile too short/long |
| `MODIFICATION_ERROR` | Error applying modifications: {details} | 400 Bad Request | Invalid modification |

---

## Version History

### Version 1.0.0 (October 14, 2025)
- Initial release with 7 MCP tools
- Complete utility function library
- Harmonics analysis support
- Inverter control utilities
- Professional visualization capabilities

---

## Support

For issues and questions:

- **GitHub Issues:** https://github.com/ahmedelshazly27/opendss-mcp-server/issues
- **Documentation:** See [USER_GUIDE.md](USER_GUIDE.md) for usage examples
- **Installation:** See [INSTALLATION.md](INSTALLATION.md) for setup instructions

---

**End of API Reference**
