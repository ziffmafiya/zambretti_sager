"""Constants for the Zambretti & Sager integration."""

from __future__ import annotations

from typing import Final

# Re-export algorithmic functions and tables for backward compatibility
from .algorithms import (
    _SAGER_WIND_TABLE,
    SAGER_TREND_RAPID,
    SAGER_TREND_SLOW,
    WIND_COMPASS,
    WIND_QUADRANTS,
    ZAMBRETTI_MAPPING,
    _get_wind_modifier,
    calculate_extrapolations,
    calculate_precipitation_probability,
    calculate_sager_forecast,
    calculate_zambretti_index,
    classify_pressure_trend,
    get_trend_label,
    wind_degrees_to_compass,
)

DOMAIN: Final[str] = "zambretti_sager"

VERSION: Final[str] = "1.9.89"

# Frontend (Lovelace card)
URL_BASE: Final[str] = "/zambretti_sager_card"

JSMODULES: Final[list[dict[str, str]]] = [
    {
        "name": "Zambretti Weather Card",
        "filename": "zambretti-weather-card.js",
        "version": VERSION,
    },
]

# Config entry keys
CONF_PRESSURE_SENSOR: Final[str] = "pressure_sensor"
CONF_WIND_SENSOR: Final[str] = "wind_sensor"
CONF_WIND_SPEED_SENSOR: Final[str] = "wind_speed_sensor"
CONF_TEMPERATURE_SENSOR: Final[str] = "temperature_sensor"
CONF_HUMIDITY_SENSOR: Final[str] = "humidity_sensor"
CONF_LATITUDE: Final[str] = "latitude"
CONF_LONGITUDE: Final[str] = "longitude"
CONF_LOCATION: Final[str] = "location"
CONF_USE_SEA_LEVEL: Final[str] = "use_sea_level_correction"

# Keywords in entity_id or attributes that suggest the sensor already reports
# sea-level pressure (MSLP/QNH), so we shouldn't apply altitude correction again
SEA_LEVEL_SENSOR_HINTS: Final[tuple[str, ...]] = (
    "sea_level",
    "sealevel",
    "mslp",
    "relative",
    "qnh",
    "barometric",
)

__all__ = [
    "CONF_HUMIDITY_SENSOR",
    "CONF_LATITUDE",
    "CONF_LOCATION",
    "CONF_LONGITUDE",
    "CONF_PRESSURE_SENSOR",
    "CONF_TEMPERATURE_SENSOR",
    "CONF_USE_SEA_LEVEL",
    "CONF_WIND_SENSOR",
    "CONF_WIND_SPEED_SENSOR",
    "DOMAIN",
    "JSMODULES",
    "SAGER_TREND_RAPID",
    "SAGER_TREND_SLOW",
    "SEA_LEVEL_SENSOR_HINTS",
    "URL_BASE",
    "VERSION",
    "WIND_COMPASS",
    "WIND_QUADRANTS",
    "ZAMBRETTI_MAPPING",
    "_SAGER_WIND_TABLE",
    "_get_wind_modifier",
    "calculate_extrapolations",
    "calculate_precipitation_probability",
    "calculate_sager_forecast",
    "calculate_zambretti_index",
    "classify_pressure_trend",
    "get_trend_label",
    "wind_degrees_to_compass",
]
