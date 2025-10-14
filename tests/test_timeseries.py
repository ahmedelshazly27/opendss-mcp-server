"""
Unit tests for time-series simulation functionality.
"""

import pytest
from opendss_mcp.tools.feeder_loader import load_ieee_test_feeder
from opendss_mcp.tools.timeseries import run_time_series_simulation
import opendssdirect as dss


def test_timeseries_24_hours():
    """Test 24-hour time-series simulation with basic load profile."""
    # Load feeder
    load_result = load_ieee_test_feeder("IEEE13")
    assert load_result["success"], f"Failed to load feeder: {load_result.get('errors')}"

    # Run 24-hour simulation with residential summer profile
    result = run_time_series_simulation(
        load_profile="residential_summer",
        duration_hours=24,
        timestep_minutes=60
    )

    # Verify success
    assert result["success"], f"Simulation failed: {result.get('errors')}"

    # Verify 24 timesteps in results
    assert "data" in result
    assert "timesteps" in result["data"]
    timesteps = result["data"]["timesteps"]
    assert len(timesteps) == 24, f"Expected 24 timesteps, got {len(timesteps)}"

    # Verify timestep structure
    for i, ts in enumerate(timesteps):
        assert "timestep" in ts
        assert ts["timestep"] == i
        assert "hour" in ts
        assert 0 <= ts["hour"] <= 24
        assert "load_multiplier" in ts
        assert "total_load_kw" in ts
        assert "converged" in ts

    # Verify load multipliers vary over time
    multipliers = [ts["load_multiplier"] for ts in timesteps]
    assert min(multipliers) < max(multipliers), "Load multipliers should vary over time"


def test_timeseries_with_solar():
    """Test time-series simulation with solar generation profile."""
    # Load feeder
    load_ieee_test_feeder("IEEE13")

    # Add a PV system to the circuit
    dss.Text.Command("New PVSystem.TestPV Bus1=675 Phases=3 kV=4.16 kVA=500 Pmpp=500 irradiance=1.0")

    # Run simulation with both load and solar profiles
    result = run_time_series_simulation(
        load_profile="residential_summer",
        generation_profile="solar_clear_day",
        duration_hours=24,
        timestep_minutes=60
    )

    # Verify success
    assert result["success"]

    # Verify generation multipliers are present
    timesteps = result["data"]["timesteps"]
    assert len(timesteps) == 24

    for ts in timesteps:
        assert "generation_multiplier" in ts
        gen_mult = ts["generation_multiplier"]
        assert 0.0 <= gen_mult <= 1.0, f"Generation multiplier {gen_mult} out of range"

    # Verify solar profile shape (zero at night, peak during day)
    night_timesteps = [timesteps[0], timesteps[1], timesteps[22], timesteps[23]]  # Midnight, 1am, 10pm, 11pm
    day_timesteps = [timesteps[11], timesteps[12]]  # Noon, 1pm

    for ts in night_timesteps:
        assert ts["generation_multiplier"] == 0.0, "Solar should be zero at night"

    for ts in day_timesteps:
        assert ts["generation_multiplier"] > 0.7, "Solar should be high at midday"

    # Verify profile names in results
    assert "profiles_applied" in result["data"]
    profiles = result["data"]["profiles_applied"]
    assert profiles["load_profile_name"] == "RESIDENTIAL_SUMMER"
    assert profiles["generation_profile_name"] == "SOLAR_CLEAR_DAY"


def test_summary_statistics():
    """Test that summary statistics are correctly calculated."""
    # Load feeder
    load_ieee_test_feeder("IEEE13")

    # Run simulation
    result = run_time_series_simulation(
        load_profile="residential_summer",
        duration_hours=24,
        timestep_minutes=60
    )

    assert result["success"]

    # Verify summary section exists
    assert "summary" in result["data"]
    summary = result["data"]["summary"]

    # Verify all required summary statistics are present
    required_fields = [
        "duration_hours",
        "num_timesteps",
        "avg_losses_kw",
        "peak_losses_kw",
        "peak_load_kw",
        "energy_served_kwh",
        "min_voltage_pu",
        "max_voltage_pu",
        "avg_voltage_pu",
        "convergence_rate_pct"
    ]

    for field in required_fields:
        assert field in summary, f"Missing summary field: {field}"

    # Verify summary values are reasonable
    assert summary["duration_hours"] == 24
    assert summary["num_timesteps"] == 24

    # Check losses are positive
    assert summary["avg_losses_kw"] > 0, "Average losses should be positive"
    assert summary["peak_losses_kw"] > 0, "Peak losses should be positive"
    assert summary["peak_losses_kw"] >= summary["avg_losses_kw"], \
        "Peak losses should be >= average losses"

    # Check load statistics
    assert summary["peak_load_kw"] > 0, "Peak load should be positive"
    assert summary["energy_served_kwh"] > 0, "Energy served should be positive"

    # Check voltage statistics
    assert 0.9 <= summary["min_voltage_pu"] <= 1.1, "Min voltage should be reasonable"
    assert 0.9 <= summary["max_voltage_pu"] <= 1.1, "Max voltage should be reasonable"
    assert summary["min_voltage_pu"] <= summary["avg_voltage_pu"] <= summary["max_voltage_pu"], \
        "Average voltage should be between min and max"

    # Check convergence rate
    assert 0 <= summary["convergence_rate_pct"] <= 100, "Convergence rate should be 0-100%"
    assert summary["convergence_rate_pct"] == 100.0, "All timesteps should converge for IEEE13"


def test_custom_profile_dict():
    """Test time-series simulation with custom profile dictionary."""
    # Load feeder
    load_ieee_test_feeder("IEEE13")

    # Create custom profile with constant 50% load
    custom_profile = {
        "name": "CUSTOM_CONSTANT",
        "multipliers": [0.5] * 24
    }

    # Run simulation
    result = run_time_series_simulation(
        load_profile=custom_profile,
        duration_hours=24,
        timestep_minutes=60
    )

    assert result["success"]

    # Verify all timesteps have multiplier of 0.5
    timesteps = result["data"]["timesteps"]
    for ts in timesteps:
        assert ts["load_multiplier"] == 0.5, "All multipliers should be 0.5"

    # Verify profile name
    assert result["data"]["profiles_applied"]["load_profile_name"] == "CUSTOM_CONSTANT"


def test_different_timestep_resolution():
    """Test time-series simulation with different timestep resolutions."""
    # Load feeder
    load_ieee_test_feeder("IEEE13")

    # Run with 30-minute timesteps (should get 48 timesteps for 24 hours)
    result = run_time_series_simulation(
        load_profile="residential_summer",
        duration_hours=24,
        timestep_minutes=30
    )

    assert result["success"]

    # Should have 48 timesteps (24 hours * 2 per hour)
    timesteps = result["data"]["timesteps"]
    assert len(timesteps) == 48, f"Expected 48 timesteps, got {len(timesteps)}"

    # Verify hour increments are correct (0.5 hour steps)
    for i, ts in enumerate(timesteps):
        expected_hour = i * 0.5
        assert abs(ts["hour"] - expected_hour) < 0.01, \
            f"Timestep {i} hour should be {expected_hour}, got {ts['hour']}"

    # Verify summary reflects correct resolution
    summary = result["data"]["summary"]
    assert summary["num_timesteps"] == 48
    assert summary["timestep_minutes"] == 30


def test_output_variables_selection():
    """Test selecting specific output variables."""
    # Load feeder
    load_ieee_test_feeder("IEEE13")

    # Run with only losses output
    result = run_time_series_simulation(
        load_profile="residential_summer",
        duration_hours=24,
        timestep_minutes=60,
        output_variables=["losses"]
    )

    assert result["success"]

    # Verify losses are present but voltages/loadings are not
    timesteps = result["data"]["timesteps"]
    first_ts = timesteps[0]

    assert "losses_kw" in first_ts, "Losses should be present"
    assert "min_voltage_pu" not in first_ts, "Voltages should not be present"
    assert "max_line_loading_pct" not in first_ts, "Loadings should not be present"


def test_output_variables_all():
    """Test with all output variables enabled."""
    # Load feeder
    load_ieee_test_feeder("IEEE13")

    # Run with all output variables
    result = run_time_series_simulation(
        load_profile="residential_summer",
        duration_hours=24,
        timestep_minutes=60,
        output_variables=["voltages", "losses", "loadings", "powers"]
    )

    assert result["success"]

    # Verify all output variables are present
    timesteps = result["data"]["timesteps"]
    first_ts = timesteps[0]

    assert "losses_kw" in first_ts
    assert "min_voltage_pu" in first_ts
    assert "max_voltage_pu" in first_ts
    assert "avg_voltage_pu" in first_ts
    assert "max_line_loading_pct" in first_ts
    assert "bus_powers" in first_ts
    assert isinstance(first_ts["bus_powers"], dict)


def test_energy_calculation():
    """Test that energy served is calculated correctly."""
    # Load feeder
    load_ieee_test_feeder("IEEE13")

    # Run simulation
    result = run_time_series_simulation(
        load_profile="residential_summer",
        duration_hours=24,
        timestep_minutes=60
    )

    assert result["success"]

    summary = result["data"]["summary"]
    timesteps = result["data"]["timesteps"]

    # Calculate energy manually for verification
    # Energy = sum(power * time) for each timestep
    timestep_hours = 1.0  # 60 minutes
    manual_energy = sum(ts["total_load_kw"] * timestep_hours for ts in timesteps)

    # Should match the reported energy_served_kwh
    assert abs(summary["energy_served_kwh"] - manual_energy) < 0.1, \
        f"Energy mismatch: {summary['energy_served_kwh']} vs {manual_energy}"


def test_peak_load_timing():
    """Test that peak load occurs at expected time."""
    # Load feeder
    load_ieee_test_feeder("IEEE13")

    # Run simulation with residential summer (peak at hour 16 = 5 PM)
    result = run_time_series_simulation(
        load_profile="residential_summer",
        duration_hours=24,
        timestep_minutes=60
    )

    assert result["success"]

    timesteps = result["data"]["timesteps"]
    summary = result["data"]["summary"]

    # Find timestep with maximum load
    max_load = max(ts["total_load_kw"] for ts in timesteps)
    peak_timestep = next(ts for ts in timesteps if ts["total_load_kw"] == max_load)

    # Should match summary peak_load_kw
    assert abs(max_load - summary["peak_load_kw"]) < 0.01

    # For residential summer, peak should be around hour 16 (5 PM)
    # Multiplier is 1.0 at hour 16
    assert 15 <= peak_timestep["hour"] <= 17, \
        f"Peak load at hour {peak_timestep['hour']}, expected around hour 16"


def test_no_generation_profile():
    """Test simulation without generation profile."""
    # Load feeder
    load_ieee_test_feeder("IEEE13")

    # Run without generation profile
    result = run_time_series_simulation(
        load_profile="residential_summer",
        generation_profile=None,
        duration_hours=24
    )

    assert result["success"]

    # Verify generation multipliers are zero
    timesteps = result["data"]["timesteps"]
    for ts in timesteps:
        assert ts["generation_multiplier"] == 0.0

    # Verify generation profile name is None
    assert result["data"]["profiles_applied"]["generation_profile_name"] is None


def test_invalid_profile_name():
    """Test handling of invalid profile name."""
    # Load feeder
    load_ieee_test_feeder("IEEE13")

    # Run with non-existent profile
    result = run_time_series_simulation(
        load_profile="nonexistent_profile",
        duration_hours=24
    )

    # Should fail gracefully
    assert not result["success"]
    assert len(result["errors"]) > 0
    assert "not found" in result["errors"][0].lower()


def test_no_circuit_loaded():
    """Test handling when no circuit is loaded."""
    # Clear any existing circuit
    dss.Text.Command("Clear")

    # Try to run simulation without loading feeder
    result = run_time_series_simulation(
        load_profile="residential_summer",
        duration_hours=24
    )

    # Should fail with appropriate error
    assert not result["success"]
    assert len(result["errors"]) > 0
    assert "no circuit loaded" in result["errors"][0].lower()


def test_short_duration_simulation():
    """Test simulation with short duration (< 24 hours)."""
    # Load feeder
    load_ieee_test_feeder("IEEE13")

    # Run 6-hour simulation
    result = run_time_series_simulation(
        load_profile="residential_summer",
        duration_hours=6,
        timestep_minutes=60
    )

    assert result["success"]

    # Should have 6 timesteps
    timesteps = result["data"]["timesteps"]
    assert len(timesteps) == 6

    # Verify hours are 0-5
    hours = [ts["hour"] for ts in timesteps]
    assert hours == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]


def test_long_duration_simulation():
    """Test simulation longer than profile length (profile repeats)."""
    # Load feeder
    load_ieee_test_feeder("IEEE13")

    # Run 48-hour simulation (2 days)
    result = run_time_series_simulation(
        load_profile="residential_summer",
        duration_hours=48,
        timestep_minutes=60
    )

    assert result["success"]

    # Should have 48 timesteps
    timesteps = result["data"]["timesteps"]
    assert len(timesteps) == 48

    # Verify profile repeats (hour 0 and hour 24 should have same multiplier)
    assert timesteps[0]["load_multiplier"] == timesteps[24]["load_multiplier"], \
        "Profile should repeat after 24 hours"


def test_voltage_statistics():
    """Test voltage statistics across time-series."""
    # Load feeder
    load_ieee_test_feeder("IEEE13")

    # Run simulation
    result = run_time_series_simulation(
        load_profile="residential_summer",
        duration_hours=24,
        timestep_minutes=60,
        output_variables=["voltages", "losses"]
    )

    assert result["success"]

    timesteps = result["data"]["timesteps"]
    summary = result["data"]["summary"]

    # Collect all min voltages across timesteps
    min_voltages = [ts["min_voltage_pu"] for ts in timesteps]
    max_voltages = [ts["max_voltage_pu"] for ts in timesteps]

    # Summary should capture the overall minimum and maximum
    overall_min = min(min_voltages)
    overall_max = max(max_voltages)

    assert abs(summary["min_voltage_pu"] - overall_min) < 0.01, \
        f"Summary min voltage {summary['min_voltage_pu']} should match overall min {overall_min}"
    assert abs(summary["max_voltage_pu"] - overall_max) < 0.01, \
        f"Summary max voltage {summary['max_voltage_pu']} should match overall max {overall_max}"


def test_line_loading_statistics():
    """Test line loading statistics."""
    # Load feeder
    load_ieee_test_feeder("IEEE13")

    # Run simulation
    result = run_time_series_simulation(
        load_profile="commercial_weekday",
        duration_hours=24,
        timestep_minutes=60,
        output_variables=["loadings"]
    )

    assert result["success"]

    timesteps = result["data"]["timesteps"]
    summary = result["data"]["summary"]

    # Verify line loading is present
    assert "max_line_loading_pct" in summary
    assert summary["max_line_loading_pct"] > 0

    # Collect all max loadings
    max_loadings = [ts["max_line_loading_pct"] for ts in timesteps]

    # Summary should capture the overall maximum
    overall_max = max(max_loadings)
    assert abs(summary["max_line_loading_pct"] - overall_max) < 0.01


def test_convergence_rate():
    """Test convergence rate calculation."""
    # Load feeder
    load_ieee_test_feeder("IEEE13")

    # Run simulation
    result = run_time_series_simulation(
        load_profile="residential_summer",
        duration_hours=24,
        timestep_minutes=60
    )

    assert result["success"]

    summary = result["data"]["summary"]

    # Verify convergence rate
    assert "convergence_rate_pct" in summary
    assert summary["convergence_rate_pct"] == 100.0, \
        "IEEE13 should converge at all timesteps"

    # Count converged timesteps manually
    timesteps = result["data"]["timesteps"]
    converged_count = sum(1 for ts in timesteps if ts["converged"])
    expected_rate = (converged_count / len(timesteps)) * 100

    assert abs(summary["convergence_rate_pct"] - expected_rate) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
