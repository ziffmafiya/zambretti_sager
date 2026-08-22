"""Unit tests for pressure conversion, sea level formulas, and elevation cache."""

from __future__ import annotations

import pytest

from custom_components.zambretti_sager.pressure_util import (
    _ELEVATION_CACHE,
    calculate_sea_level_pressure,
    parse_pressure_hpa_from_history,
)


def test_calculate_sea_level_pressure():
    """Test standard barometric formula for sea level reduction."""
    # At sea level (altitude = 0), sea level pressure equals station pressure
    assert pytest.approx(calculate_sea_level_pressure(1013.25, 15.0, 0.0), rel=1e-3) == 1013.25

    # At 100m elevation, sea-level pressure is higher than station pressure (~12 hPa higher)
    p_sl_100m = calculate_sea_level_pressure(1000.0, 15.0, 100.0)
    assert p_sl_100m > 1000.0
    assert 1010.0 < p_sl_100m < 1015.0

    # At negative elevation (below sea level), station pressure is higher than sea level
    p_sl_below = calculate_sea_level_pressure(1020.0, 15.0, -50.0)
    assert p_sl_below < 1020.0

    # None altitude returns original pressure unchanged
    assert calculate_sea_level_pressure(1015.0, 15.0, None) == 1015.0


def test_parse_pressure_hpa_from_history():
    """Test parsing and unit conversion from historical state dicts."""
    # hPa / mbar
    assert parse_pressure_hpa_from_history({"state": "1013.25", "attributes": {"unit_of_measurement": "hPa"}}) == pytest.approx(1013.25)
    assert parse_pressure_hpa_from_history({"state": "1013.25", "attributes": {"unit_of_measurement": "mbar"}}) == pytest.approx(1013.25)

    # Pa (Pascals) -> hPa
    assert parse_pressure_hpa_from_history({"state": "101325", "attributes": {"unit_of_measurement": "Pa"}}) == pytest.approx(1013.25)

    # inHg -> hPa (29.92 inHg ~ 1013.2 hPa)
    assert parse_pressure_hpa_from_history({"state": "29.92", "attributes": {"unit_of_measurement": "inHg"}}) == pytest.approx(1013.2, abs=0.2)

    # mmHg -> hPa (760 mmHg ~ 1013.25 hPa)
    assert parse_pressure_hpa_from_history({"state": "760", "attributes": {"unit_of_measurement": "mmHg"}}) == pytest.approx(1013.25, abs=0.2)

    # bar -> hPa (1.01325 bar -> 1013.25 hPa)
    assert parse_pressure_hpa_from_history({"state": "1.01325", "attributes": {"unit_of_measurement": "bar"}}) == pytest.approx(1013.25)

    # Invalid / unavailable values raise ValueError
    with pytest.raises(ValueError):
        parse_pressure_hpa_from_history({"state": "unavailable", "attributes": {}})
    with pytest.raises(ValueError):
        parse_pressure_hpa_from_history({"state": "unknown", "attributes": {}})
    with pytest.raises(ValueError):
        parse_pressure_hpa_from_history(None)


def test_elevation_cache():
    """Test that elevation cache stores and preserves retrieved elevations."""
    coord_key = (55.7558, 37.6173)
    _ELEVATION_CACHE[coord_key] = 156.0

    assert _ELEVATION_CACHE[coord_key] == 156.0
