"""Unit tests for config flow helpers and validation."""

from __future__ import annotations

from custom_components.zambretti_sager.config_flow import (
    _apply_location,
    _normalize_optional_entities,
)
from custom_components.zambretti_sager.const import (
    CONF_HUMIDITY_SENSOR,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_PRESSURE_SENSOR,
    CONF_TEMPERATURE_SENSOR,
    CONF_WIND_SENSOR,
    CONF_WIND_SPEED_SENSOR,
)


def test_apply_location():
    """Test extracting latitude and longitude from location map dict."""
    user_input = {
        CONF_PRESSURE_SENSOR: "sensor.barometer",
        CONF_LOCATION: {"latitude": 59.93, "longitude": 30.33},
    }
    processed = _apply_location(user_input)

    assert CONF_LATITUDE in processed
    assert CONF_LONGITUDE in processed
    assert processed[CONF_LATITUDE] == 59.93
    assert processed[CONF_LONGITUDE] == 30.33
    assert CONF_LOCATION not in processed


def test_normalize_optional_entities():
    """Test converting empty string optional sensor fields to None."""
    user_input = {
        CONF_PRESSURE_SENSOR: "sensor.barometer",
        CONF_WIND_SENSOR: "",
        CONF_WIND_SPEED_SENSOR: "  ",
        CONF_TEMPERATURE_SENSOR: "sensor.temp",
        CONF_HUMIDITY_SENSOR: None,
    }
    normalized = _normalize_optional_entities(user_input)

    assert normalized[CONF_PRESSURE_SENSOR] == "sensor.barometer"
    assert CONF_WIND_SENSOR not in normalized
    assert CONF_WIND_SPEED_SENSOR not in normalized
    assert normalized[CONF_TEMPERATURE_SENSOR] == "sensor.temp"
    assert CONF_HUMIDITY_SENSOR not in normalized
