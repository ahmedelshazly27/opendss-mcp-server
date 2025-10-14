# Load Profiles

This directory contains time-series load and generation profiles for OpenDSS simulations. These profiles define how loads and distributed energy resources (DERs) vary over time.

## Overview

Load profiles are essential for time-series power flow analysis, showing how electrical demand and generation change throughout the day. OpenDSS uses these profiles as multipliers applied to base power values.

## Available Profiles

### Load Profiles

#### 1. Residential Summer (`residential_summer.json`)
**Characteristics:**
- Peak at 5 PM (hour 16): 1.0 pu
- Morning ramp-up: 6-8 AM
- Evening peak: 4-8 PM
- Minimum at 3-4 AM: 0.3 pu

**Typical Applications:**
- Single-family homes
- Apartment buildings
- Residential neighborhoods
- Summer air conditioning loads

#### 2. Residential Winter (`residential_winter.json`)
**Characteristics:**
- Peak at 6 PM (hour 17): 1.0 pu
- Higher nighttime base load (0.4-0.5 pu) due to heating
- Morning peak: 6-8 AM
- Evening peak: 5-7 PM

**Typical Applications:**
- Residential heating loads
- Electric resistance heating
- Heat pump systems
- Cold climate load patterns

#### 3. Commercial Weekday (`commercial_weekday.json`)
**Characteristics:**
- Peak during business hours: 10 AM - 2 PM
- Sustained plateau: 0.95-1.0 pu from 9 AM - 5 PM
- Morning ramp-up: 7-9 AM
- Evening ramp-down: 5-7 PM
- Nighttime base load: 0.25-0.3 pu

**Typical Applications:**
- Office buildings
- Retail stores
- Business districts
- Commercial HVAC systems

#### 4. Commercial Weekend (`commercial_weekend.json`)
**Characteristics:**
- Reduced load: 50% of weekday peak
- Flat profile: minimal variation
- Base load: 0.2-0.5 pu
- No significant peaks

**Typical Applications:**
- Unoccupied office buildings
- Reduced HVAC setback mode
- Security and emergency systems
- Weekend maintenance operations

### Generation Profiles

#### 5. Solar Clear Day (`solar_clear_day.json`)
**Characteristics:**
- Peak at solar noon (hour 11): 1.0 pu
- Bell curve shape
- Sunrise: ~6 AM (hour 5)
- Sunset: ~6 PM (hour 17)
- Zero generation at night

**Typical Applications:**
- Rooftop solar PV systems
- Utility-scale solar farms
- Clear sky conditions
- Peak irradiance scenarios

#### 6. Solar Cloudy Day (`solar_cloudy_day.json`)
**Characteristics:**
- Reduced peak: 0.7 pu (70% of clear day)
- Irregular profile with variability
- Overall 30-40% reduction in generation
- Variable afternoon output

**Typical Applications:**
- Partly cloudy conditions
- Intermittent cloud cover
- Conservative solar forecasting
- Sensitivity analysis

## File Format

All profiles follow this JSON schema:

```json
{
  "name": "PROFILE_NAME",
  "description": "Human-readable description",
  "type": "load | generation",
  "interval": "hourly",
  "units": "per-unit",
  "multipliers": [
    0.4, 0.35, 0.3, ..., 0.5
  ],
  "notes": ["Optional notes array"]
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique profile identifier (uppercase, underscores) |
| `description` | string | Yes | Human-readable profile description |
| `type` | string | Yes | Profile type: "load" or "generation" |
| `interval` | string | Yes | Time interval: "hourly" (24 points) |
| `units` | string | Yes | "per-unit" (normalized multipliers) |
| `multipliers` | array | Yes | 24 hourly multiplier values [0.0 - 1.0+] |
| `season` | string | No | Season: "summer", "winter" (for load profiles) |
| `day_type` | string | No | Day type: "weekday", "weekend" |
| `building_type` | string | No | Building type: "residential", "commercial" |
| `resource_type` | string | No | Resource: "solar", "wind" (for generation) |
| `weather` | string | No | Weather: "clear", "cloudy" |
| `notes` | array | No | Additional information or usage notes |

### Multipliers Format

The `multipliers` array contains 24 values representing each hour of the day:

**Hour Indexing:**
- Hour 0 = Midnight (12:00 AM - 1:00 AM)
- Hour 1 = 1:00 AM - 2:00 AM
- ...
- Hour 11 = 11:00 AM - 12:00 PM (noon)
- Hour 12 = 12:00 PM - 1:00 PM
- ...
- Hour 23 = 11:00 PM - Midnight

**Multiplier Values:**
- Per-unit (pu) of base load/generation
- Typically normalized so peak = 1.0
- Load profiles: usually 0.3 - 1.0 pu
- Generation profiles: 0.0 - 1.0 pu
- Values > 1.0 are allowed for exceptional peaks

**How Multipliers Work:**

If a load has a base power of 100 kW and the profile multiplier at hour 16 is 1.0:
```
Actual Load = Base Load × Multiplier = 100 kW × 1.0 = 100 kW
```

If the multiplier at hour 3 is 0.3:
```
Actual Load = 100 kW × 0.3 = 30 kW
```

## Using Profiles in OpenDSS

### Method 1: LoadShape Object

```python
import opendssdirect as dss
import json
from pathlib import Path

# Load profile from JSON
profile_path = Path("src/opendss_mcp/data/load_profiles/residential_summer.json")
with open(profile_path) as f:
    profile = json.load(f)

# Create LoadShape in OpenDSS
multipliers_str = str(profile["multipliers"]).replace("[", "(").replace("]", ")")
dss.Text.Command(
    f"New LoadShape.ResidentialSummer "
    f"npts=24 "
    f"interval=1 "
    f"mult={multipliers_str}"
)

# Apply to a load
dss.Text.Command(
    f"New Load.House1 Bus1=650 "
    f"Phases=1 kV=2.4 kW=10 PF=0.95 "
    f"Daily=ResidentialSummer"
)
```

### Method 2: Direct Assignment

```python
# Load profile
with open("residential_summer.json") as f:
    profile = json.load(f)
    multipliers = profile["multipliers"]

# For each hour, scale the load
for hour in range(24):
    mult = multipliers[hour]
    # Update load power
    dss.Text.Command(f"Load.House1.kW={10.0 * mult}")
    dss.Solution.Solve()
    # Process results...
```

## Creating Custom Profiles

### Step 1: Define Your Profile

```json
{
  "name": "MY_CUSTOM_PROFILE",
  "description": "Description of your load/generation pattern",
  "type": "load",
  "interval": "hourly",
  "units": "per-unit",
  "multipliers": [
    0.5, 0.4, 0.3, 0.3, 0.4, 0.5, 0.7, 0.9, 1.0, 0.9, 0.8, 0.7,
    0.7, 0.8, 0.9, 1.0, 0.95, 0.9, 0.8, 0.7, 0.6, 0.6, 0.55, 0.5
  ],
  "notes": ["Custom profile notes"]
}
```

### Step 2: Validation Rules

- **Exactly 24 values** required for hourly profiles
- **Non-negative values** for most applications
- **Peak normalized to 1.0** (recommended for consistency)
- **Smooth transitions** preferred (avoid abrupt jumps)
- **Realistic patterns** based on physical behavior

### Step 3: Best Practices

1. **Normalize to Peak:**
   ```python
   # Normalize multipliers so max = 1.0
   max_value = max(multipliers)
   normalized = [m / max_value for m in multipliers]
   ```

2. **Validate Sum:**
   ```python
   # Daily energy should be reasonable
   daily_energy = sum(multipliers)  # Sum of all 24 hours
   average_load = daily_energy / 24  # Should be ~0.5-0.8 for typical loads
   ```

3. **Check Smoothness:**
   ```python
   # Avoid large hour-to-hour jumps
   for i in range(1, 24):
       change = abs(multipliers[i] - multipliers[i-1])
       assert change < 0.3, f"Large jump at hour {i}: {change}"
   ```

4. **Physical Plausibility:**
   - Residential: Low at night (0.3-0.5), peaks morning/evening
   - Commercial: Low at night (0.2-0.3), high during business hours
   - Solar: Zero at night, bell curve during day
   - Wind: Can be variable, but typically smoother

## Common Use Cases

### Time-Series Power Flow Analysis

```python
# Load feeder
load_ieee_test_feeder("IEEE13")

# Load residential profile
with open("residential_summer.json") as f:
    profile = json.load(f)

# Run 24-hour simulation
results = []
for hour in range(24):
    mult = profile["multipliers"][hour]

    # Scale all residential loads
    for load_name in dss.Loads.AllNames():
        if "residential" in load_name.lower():
            base_kw = 10.0  # Base load
            dss.Loads.Name(load_name)
            dss.Loads.kW(base_kw * mult)

    # Solve and collect results
    dss.Solution.Solve()
    results.append({
        "hour": hour,
        "losses_kw": dss.Circuit.Losses()[0] / 1000,
        "load_mult": mult
    })
```

### Solar + Load Net Load Profile

```python
# Calculate net load (load - generation)
with open("residential_summer.json") as f:
    load_profile = json.load(f)["multipliers"]

with open("solar_clear_day.json") as f:
    solar_profile = json.load(f)["multipliers"]

# Net load = Load - Solar
net_load = [load_profile[h] - solar_profile[h] for h in range(24)]

# Identify peak net load hour
peak_hour = net_load.index(max(net_load))
print(f"Peak net load at hour {peak_hour}: {net_load[peak_hour]:.2f} pu")
```

### Duck Curve Analysis

```python
import matplotlib.pyplot as plt

# Plot the "duck curve" effect
hours = list(range(24))
plt.figure(figsize=(10, 6))
plt.plot(hours, load_profile, label="Load", linewidth=2)
plt.plot(hours, solar_profile, label="Solar Generation", linewidth=2)
plt.plot(hours, net_load, label="Net Load (Duck Curve)", linewidth=2, linestyle="--")
plt.xlabel("Hour of Day")
plt.ylabel("Power (pu)")
plt.title("Duck Curve: Load vs Net Load with Solar")
plt.legend()
plt.grid(True)
plt.show()
```

## Standards & References

- **EPRI Load Modeling:** Load shape recommendations for distribution analysis
- **NREL TMY3 Data:** Typical Meteorological Year solar irradiance data
- **OpenDSS LoadShape Documentation:** [OpenDSS LoadShape Object](https://opendss.epri.com/LoadShape.html)
- **IEEE 399-1997:** Recommended Practice for Power System Analysis (Brown Book)

## Profile Characteristics Summary

| Profile | Type | Peak Hour | Peak Value | Min Value | Daily Avg |
|---------|------|-----------|------------|-----------|-----------|
| Residential Summer | Load | 16 (5 PM) | 1.00 | 0.30 | 0.66 |
| Residential Winter | Load | 17 (6 PM) | 1.00 | 0.40 | 0.70 |
| Commercial Weekday | Load | 10-14 | 1.00 | 0.25 | 0.65 |
| Commercial Weekend | Load | 11-12 | 0.50 | 0.20 | 0.29 |
| Solar Clear Day | Gen | 11 (noon) | 1.00 | 0.00 | 0.33 |
| Solar Cloudy Day | Gen | 11 (noon) | 0.70 | 0.00 | 0.23 |

## Additional Resources

- [OpenDSS Simulation Basics](https://opendss.epri.com/)
- [NREL Solar Data](https://nsrdb.nrel.gov/)
- [EIA Electricity Data](https://www.eia.gov/electricity/)
- [Project Repository](https://github.com/ahmedelshazly27/opendss-mcp-server)

## Support

For questions or to request additional load profiles:
1. Check existing profiles for similar patterns
2. Review the custom profile creation section
3. File an issue on the project repository

---

**Note:** All profiles are representative examples for simulation purposes. Actual load and generation patterns vary significantly based on location, climate, building characteristics, occupancy, and equipment. For critical applications, use measured data or validated load research studies specific to your region.
