"""Unit tests for Zambretti, Sager, and weather forecasting algorithms."""

from __future__ import annotations

from custom_components.zambretti_sager.const import (
    ZAMBRETTI_MAPPING,
    calculate_precipitation_probability,
    calculate_sager_forecast,
    calculate_zambretti_index,
    classify_pressure_trend,
    get_trend_label,
    wind_degrees_to_compass,
)


def test_classify_pressure_trend():
    """Test classification of pressure trends."""
    assert classify_pressure_trend(4.0) == "rising_rapidly"
    assert classify_pressure_trend(1.5) == "rising_rapidly"
    assert classify_pressure_trend(1.0) == "rising_slowly"
    assert classify_pressure_trend(0.7) == "rising_slowly"
    assert classify_pressure_trend(0.5) == "steady"
    assert classify_pressure_trend(0.0) == "steady"
    assert classify_pressure_trend(-0.5) == "steady"
    assert classify_pressure_trend(-0.7) == "falling_slowly"
    assert classify_pressure_trend(-1.0) == "falling_slowly"
    assert classify_pressure_trend(-1.5) == "falling_rapidly"
    assert classify_pressure_trend(-4.5) == "falling_rapidly"


def test_get_trend_label():
    """Test trend label formatting."""
    assert get_trend_label(3.5) == "↑↑ Rising Fast"
    assert get_trend_label(1.0) == "↑ Rising"
    assert get_trend_label(0.0) == "→ Steady"
    assert get_trend_label(-1.0) == "↓ Falling"
    assert get_trend_label(-3.5) == "↓↓ Falling Fast"


def test_calculate_zambretti_index():
    """Test Zambretti index calculation for various trends and pressures."""
    # High pressure, rising trend -> index 20 (Settled Fine)
    idx_high_rising = calculate_zambretti_index(1030.0, 2.5)
    assert 1 <= idx_high_rising <= 32
    assert idx_high_rising == 20

    # Low pressure, falling trend -> high index (Stormy/Rain)
    idx_low_falling = calculate_zambretti_index(970.0, -3.0)
    assert 1 <= idx_low_falling <= 32
    assert idx_low_falling >= 10

    # Normal pressure, steady
    idx_normal_steady = calculate_zambretti_index(1013.25, 0.0)
    assert 1 <= idx_normal_steady <= 32

    # Clamping tests
    assert calculate_zambretti_index(1200.0, 5.0) == 1
    assert calculate_zambretti_index(700.0, -5.0) == 32

    # All indices 1-32 map to valid keys or stable
    for z in range(1, 33):
        assert z in ZAMBRETTI_MAPPING


def test_calculate_precipitation_probability():
    """Test precipitation probability calculation and boundary clamping."""
    # Low pressure + falling fast + high humidity -> high probability (capped at 100)
    prob_high = calculate_precipitation_probability(980.0, -4.0, humidity=95.0)
    assert prob_high == 100

    # High pressure + rising fast + low humidity -> low probability (floored at 0)
    prob_low = calculate_precipitation_probability(1035.0, 4.0, humidity=20.0)
    assert prob_low == 0

    # Moderate conditions
    prob_mid = calculate_precipitation_probability(1012.0, 0.0, humidity=50.0)
    assert 0 <= prob_mid <= 100

    # None humidity works safely
    prob_no_hum = calculate_precipitation_probability(1010.0, -2.0, humidity=None)
    assert 0 <= prob_no_hum <= 100


def test_wind_degrees_to_compass():
    """Test conversion of degrees to 8-point compass directions."""
    assert wind_degrees_to_compass(None) is None
    assert wind_degrees_to_compass(0.0) == "N"
    assert wind_degrees_to_compass(360.0) == "N"
    assert wind_degrees_to_compass(45.0) == "NE"
    assert wind_degrees_to_compass(90.0) == "E"
    assert wind_degrees_to_compass(135.0) == "SE"
    assert wind_degrees_to_compass(180.0) == "S"
    assert wind_degrees_to_compass(225.0) == "SW"
    assert wind_degrees_to_compass(270.0) == "W"
    assert wind_degrees_to_compass(315.0) == "NW"
    assert wind_degrees_to_compass(350.0) == "N"
    assert wind_degrees_to_compass(10.0) == "N"


def test_calculate_sager_forecast():
    """Test Sager forecast table lookup."""
    # Very high pressure
    res_high = calculate_sager_forecast(1035.0, 2.0, 45.0)
    assert res_high is not None
    assert res_high.startswith("sager_")

    # Low pressure
    res_low = calculate_sager_forecast(995.0, -2.0, 225.0)
    assert res_low is not None
    assert res_low.startswith("sager_")

    # Missing wind direction falls back to standard lookup without error
    res_no_wind = calculate_sager_forecast(1013.0, 0.0, None)
    assert res_no_wind is not None
    assert res_no_wind.startswith("sager_")
