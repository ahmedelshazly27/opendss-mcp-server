# Control Curves

This directory contains volt-var control curve definitions for distributed energy resources (DER) in OpenDSS simulations.

## Overview

Volt-var curves define how inverter-based DERs (solar PV, battery storage, etc.) automatically adjust their reactive power output based on local voltage conditions. This autonomous voltage regulation helps maintain grid stability and power quality.

## Available Curves

### 1. IEEE 1547-2018 Category B (`ieee1547.json`)

The default volt-var curve from IEEE 1547-2018 standard, Category B.

**Characteristics:**
- **Voltage Range:** 0.92 - 1.08 per-unit
- **Reactive Power Range:** ±44% of rated inverter kVA
- **Deadband:** 0.98 - 1.02 pu (no reactive power in normal voltage range)

**Points:**
```
Voltage (pu)  |  Reactive Power (pu)
    0.92      |      +0.44  (absorb vars)
    0.98      |       0.00  (deadband start)
    1.02      |       0.00  (deadband end)
    1.08      |      -0.44  (inject vars)
```

**Use Case:** Standard interconnection compliance for distributed generation systems.

### 2. California Rule 21 (`rule21.json`)

California's Rule 21 default volt-var curve for smart inverters.

**Characteristics:**
- **Voltage Range:** 0.95 - 1.05 per-unit
- **Reactive Power Range:** ±44% of rated inverter kVA
- **Deadband:** 0.99 - 1.01 pu (tighter than IEEE 1547)

**Points:**
```
Voltage (pu)  |  Reactive Power (pu)
    0.95      |      +0.44  (absorb vars)
    0.99      |       0.00  (deadband start)
    1.01      |       0.00  (deadband end)
    1.05      |      -0.44  (inject vars)
```

**Use Case:** California utility interconnection requirements, provides tighter voltage regulation.

### 3. Custom Template (`custom_template.json`)

Template for creating user-defined control curves.

## Curve Format

All control curves follow this JSON schema:

```json
{
  "name": "CURVE_NAME",
  "description": "Human-readable description",
  "type": "volt-var",
  "points": [
    [voltage_pu, var_pu],
    [voltage_pu, var_pu],
    ...
  ],
  "units": {
    "voltage": "per-unit",
    "var": "per-unit (of rated kVA)"
  },
  "notes": ["Optional notes array"]
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique curve identifier (uppercase, no spaces) |
| `description` | string | Yes | Human-readable curve description |
| `type` | string | Yes | Control type (currently only "volt-var") |
| `points` | array | Yes | Array of [voltage, var] coordinate pairs |
| `units` | object | No | Unit specifications for documentation |
| `notes` | array | No | Additional information or usage notes |

### Points Format

Each point in the `points` array is a two-element array: `[voltage_pu, var_pu]`

**Voltage (first element):**
- Per-unit voltage (typically 0.90 - 1.10)
- Must be sorted in ascending order
- 1.0 = nominal voltage

**Reactive Power (second element):**
- Per-unit of rated inverter kVA
- Typical range: -0.44 to +0.44 (per IEEE 1547)
- **Positive values:** Absorb vars (inductive, lagging power factor)
- **Negative values:** Inject vars (capacitive, leading power factor)

## Creating Custom Curves

1. Copy `custom_template.json` to a new file:
   ```bash
   cp custom_template.json my_custom_curve.json
   ```

2. Edit the file with your curve parameters:
   - Change `name` to your unique curve identifier
   - Update `description` with curve purpose
   - Modify `points` array with your voltage-var pairs
   - Add custom `notes` if needed

3. **Validation Rules:**
   - Minimum 2 points required
   - Maximum 10 points recommended (for performance)
   - Points must be sorted by voltage (ascending)
   - Voltages should be within reasonable range (0.80 - 1.20 pu)
   - Var values typically ±0.44 pu (per IEEE 1547 limits)

4. **Best Practices:**
   - Include a deadband (zero var region) around 1.0 pu for stability
   - Use smooth transitions (avoid abrupt changes)
   - Consider inverter physical limits (typically ±44% of kVA rating)
   - Test curve behavior with OpenDSS simulations before deployment

## Usage Example

```python
import json
from pathlib import Path

# Load a control curve
curve_path = Path("src/opendss_mcp/data/control_curves/ieee1547.json")
with open(curve_path) as f:
    curve = json.load(f)

# Access curve data
name = curve["name"]  # "IEEE1547"
points = curve["points"]  # [[0.92, 0.44], [0.98, 0.0], ...]

# Use in OpenDSS simulation
for voltage, var in points:
    print(f"At {voltage:.2f} pu voltage: {var:+.2f} pu vars")
```

## Volt-Var Control Behavior

### How It Works

1. **Voltage Measurement:** Inverter measures local AC voltage
2. **Curve Lookup:** Interpolate reactive power setpoint from volt-var curve
3. **Power Adjustment:** Inverter adjusts reactive power output accordingly
4. **Continuous Operation:** Process repeats continuously (typically every few seconds)

### Physical Interpretation

**Low Voltage (< 1.0 pu):**
- Grid needs voltage support
- Inverter absorbs vars (positive Q)
- Acts like an inductor / lagging power factor
- Helps raise local voltage

**High Voltage (> 1.0 pu):**
- Grid has excess voltage
- Inverter injects vars (negative Q)
- Acts like a capacitor / leading power factor
- Helps lower local voltage

**Normal Voltage (deadband):**
- No reactive power adjustment needed
- Inverter operates at unity power factor
- Maximizes real power delivery

## Standards & References

- **IEEE 1547-2018:** Standard for Interconnecting Distributed Resources with Electric Power Systems
- **California Rule 21:** Smart Inverter Requirements (CPUC)
- **UL 1741 SA:** Supplement SA for Smart Inverter Testing
- **IEC 61850-90-7:** Communication networks for DER

## Additional Resources

- [IEEE 1547-2018 Overview](https://standards.ieee.org/standard/1547-2018.html)
- [CPUC Rule 21 Resources](https://www.cpuc.ca.gov/Rule21/)
- [OpenDSS XY Curve Documentation](https://opendss.epri.com/XYCurve.html)

## Support

For questions or issues with control curves:
1. Check the `custom_template.json` for formatting examples
2. Review OpenDSS documentation for XYCurve objects
3. File an issue on the project repository

---

**Note:** All curves are provided for simulation purposes. Actual deployment should follow local utility interconnection requirements and obtain appropriate approvals.
