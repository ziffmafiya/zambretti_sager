"""Constants for the Zambretti & Sager integration."""

from typing import Final

DOMAIN = "zambretti_sager"

VERSION = "1.9.72"

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
CONF_PRESSURE_SENSOR = "pressure_sensor"
CONF_WIND_SENSOR = "wind_sensor"
CONF_WIND_SPEED_SENSOR = "wind_speed_sensor"
CONF_TEMPERATURE_SENSOR = "temperature_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_USE_SEA_LEVEL = "use_sea_level_correction"

# Zambretti algorithm mapping: pressure trend index (1–32) → translation key
# The original Zambretti algorithm has 32 forecast states grouped by
# pressure trend: Falling (1-9), Steady (10-19), Rising (20-32)
ZAMBRETTI_MAPPING = {
    # Falling pressure (worsening weather)
    1: "settled_fine",
    2: "fine_weather",
    3: "fine_becoming_less_settled",
    4: "fairly_fine_showery_later",
    5: "showery_becoming_more_unsettled",
    6: "unsettled_rain_later",
    7: "rain_at_times_worse_later",
    8: "rain_at_times_becoming_very_unsettled",
    9: "very_unsettled_rain",
    # Steady pressure
    10: "settled_fine",
    11: "fine_weather",
    12: "fine_possibly_showers",
    13: "fairly_fine_showers_likely",
    14: "showery_bright_intervals",
    15: "changeable_some_rain",
    16: "unsettled_rain_at_times",
    17: "rain_at_frequent_intervals",
    18: "very_unsettled_rain",
    19: "stormy_much_rain",
    # Rising pressure (improving weather)
    20: "settled_fine",
    21: "fine_weather",
    22: "becoming_fine",
    23: "fairly_fine_improving",
    24: "fairly_fine_possibly_showers_early",
    25: "showery_early_improving",
    26: "changeable_mending",
    27: "rather_unsettled_clearing_later",
    28: "unsettled_probably_improving",
    29: "unsettled_short_fine_intervals",
    30: "very_unsettled_finer_at_times",
    31: "stormy_possibly_improving",
    32: "stormy_much_rain",
}

# Sager algorithm pressure trend thresholds (hPa over ~3 hours)
SAGER_TREND_RAPID = 1.4
SAGER_TREND_SLOW = 0.7

# 8-point wind compass directions
WIND_COMPASS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")

# Wind direction quadrants for Sager algorithm refinement
WIND_QUADRANTS: Final[dict[str, str]] = {
    "N": "northerly",
    "NE": "northerly",
    "E": "easterly",
    "SE": "easterly",
    "S": "southerly",
    "SW": "southerly",
    "W": "westerly",
    "NW": "westerly",
}

# Keywords in entity_id or attributes that suggest the sensor already reports
# sea-level pressure (MSLP/QNH), so we shouldn't apply altitude correction again
SEA_LEVEL_SENSOR_HINTS = (
    "sea_level",
    "sealevel",
    "mslp",
    "relative",
    "qnh",
    "barometric",
)


def classify_pressure_trend(delta_hpa: float) -> str:
    """Classify pressure trend for the Sager algorithm.

    Args:
        delta_hpa: Pressure change in hPa over the measurement period.

    Returns:
        One of: "rising_rapidly", "rising_slowly", "steady",
                "falling_slowly", "falling_rapidly".
    """
    if delta_hpa >= SAGER_TREND_RAPID:
        return "rising_rapidly"
    if delta_hpa >= SAGER_TREND_SLOW:
        return "rising_slowly"
    if delta_hpa <= -SAGER_TREND_RAPID:
        return "falling_rapidly"
    if delta_hpa <= -SAGER_TREND_SLOW:
        return "falling_slowly"
    return "steady"


def wind_degrees_to_compass(degrees: float | None) -> str | None:
    """Convert wind direction in degrees to 8-point compass string (N, NE, E, ...)."""
    if degrees is None:
        return None
    index = round(degrees / 45) % 8
    return WIND_COMPASS[index]


def _get_wind_modifier(wind_degrees: float | None) -> str | None:
    """Convert wind direction to a Sager wind quadrant modifier."""
    if wind_degrees is None:
        return None
    compass = wind_degrees_to_compass(wind_degrees)
    return WIND_QUADRANTS.get(compass)


# Sager wind-enhanced forecast table.
# First key = pressure zone ("fair", "unsettled", "changeable")
# Second key = trend from classify_pressure_trend()
# Third key = wind modifier or None (backward compatible fallback)
_SAGER_WIND_TABLE: Final[dict[str, dict[str, dict[str | None, str]]]] = {
    "fair": {
        "rising_rapidly": {
            None: "sager_fair_improving",
            "northerly": "sager_fair_improving",
            "easterly": "sager_fair_improving",
            "southerly": "sager_fair_tending_to_deteriorate",
            "westerly": "sager_variable_slowly_improving",
        },
        "rising_slowly": {
            None: "sager_fair_improving",
            "northerly": "sager_fair_improving",
            "easterly": "sager_fair_improving",
            "southerly": "sager_fair_tending_to_deteriorate",
            "westerly": "sager_variable_slowly_improving",
        },
        "falling_rapidly": {
            None: "sager_fair_tending_to_deteriorate",
            "northerly": "sager_fair_tending_to_deteriorate",
            "easterly": "sager_variable_slowly_deteriorating",
            "southerly": "sager_unsettled_rain_likely",
            "westerly": "sager_changeable_becoming_more_unsettled",
        },
        "falling_slowly": {
            None: "sager_fair_tending_to_deteriorate",
            "northerly": "sager_fair_tending_to_deteriorate",
            "easterly": "sager_variable_slowly_deteriorating",
            "southerly": "sager_unsettled_rain_likely",
            "westerly": "sager_changeable_becoming_more_unsettled",
        },
        "steady": {
            None: "sager_fair_no_change",
            "northerly": "sager_fair_no_change",
            "easterly": "sager_variable_some_change",
            "southerly": "sager_fair_tending_to_deteriorate",
            "westerly": "sager_variable_some_change",
        },
    },
    "unsettled": {
        "rising_rapidly": {
            None: "sager_unsettled_probably_improving",
            "northerly": "sager_unsettled_probably_improving",
            "easterly": "sager_unsettled_probably_improving",
            "southerly": "sager_unsettled_rain_at_times",
            "westerly": "sager_variable_slowly_improving",
        },
        "rising_slowly": {
            None: "sager_unsettled_probably_improving",
            "northerly": "sager_unsettled_probably_improving",
            "easterly": "sager_unsettled_probably_improving",
            "southerly": "sager_unsettled_rain_at_times",
            "westerly": "sager_variable_slowly_improving",
        },
        "falling_rapidly": {
            None: "sager_unsettled_rain_likely",
            "northerly": "sager_unsettled_rain_at_times",
            "easterly": "sager_unsettled_rain_at_times",
            "southerly": "sager_unsettled_rain_likely",
            "westerly": "sager_unsettled_rain_likely",
        },
        "falling_slowly": {
            None: "sager_unsettled_rain_likely",
            "northerly": "sager_unsettled_rain_at_times",
            "easterly": "sager_unsettled_rain_at_times",
            "southerly": "sager_unsettled_rain_likely",
            "westerly": "sager_unsettled_rain_likely",
        },
        "steady": {
            None: "sager_unsettled_rain_at_times",
            "northerly": "sager_unsettled_rain_at_times",
            "easterly": "sager_variable_some_change",
            "southerly": "sager_unsettled_rain_likely",
            "westerly": "sager_changeable_becoming_more_unsettled",
        },
    },
    "changeable": {
        "rising_rapidly": {
            None: "sager_changeable_becoming_fairer",
            "northerly": "sager_changeable_becoming_fairer",
            "easterly": "sager_changeable_becoming_fairer",
            "southerly": "sager_variable_slowly_improving",
            "westerly": "sager_variable_slowly_improving",
        },
        "falling_rapidly": {
            None: "sager_changeable_becoming_more_unsettled",
            "northerly": "sager_changeable_becoming_more_unsettled",
            "easterly": "sager_variable_slowly_deteriorating",
            "southerly": "sager_unsettled_rain_likely",
            "westerly": "sager_changeable_becoming_more_unsettled",
        },
        "rising_slowly": {
            None: "sager_variable_slowly_improving",
            "northerly": "sager_variable_slowly_improving",
            "easterly": "sager_variable_some_change",
            "southerly": "sager_fair_tending_to_deteriorate",
            "westerly": "sager_variable_some_change",
        },
        "falling_slowly": {
            None: "sager_variable_slowly_deteriorating",
            "northerly": "sager_variable_slowly_deteriorating",
            "easterly": "sager_variable_some_change",
            "southerly": "sager_unsettled_rain_likely",
            "westerly": "sager_unsettled_rain_at_times",
        },
        "steady": {
            None: "sager_variable_some_change",
            "northerly": "sager_fair_no_change",
            "easterly": "sager_variable_some_change",
            "southerly": "sager_fair_tending_to_deteriorate",
            "westerly": "sager_changeable_becoming_more_unsettled",
        },
    },
}


def calculate_sager_forecast(
    pressure_hpa: float,
    delta_hpa: float,
    wind_degrees: float | None = None,
) -> str:
    """Calculate Sager forecast with wind direction refinement.

    Uses pressure zone, 3-hour trend, and optional wind direction to select
    the most appropriate forecast state. Wind direction is grouped into four
    quadrants (northerly/easterly/southerly/westerly) that modify the base
    pressure-trend prediction.

    Args:
        pressure_hpa: Current pressure (preferably sea-level corrected) in hPa.
        delta_hpa: Pressure change over ~3 hours.
        wind_degrees: Optional wind direction in degrees.

    Returns:
        Translation key for the Sager forecast state.
    """
    trend = classify_pressure_trend(delta_hpa)
    modifier = _get_wind_modifier(wind_degrees)

    if pressure_hpa > 1020:
        zone = "fair"
    elif pressure_hpa < 1005:
        zone = "unsettled"
    else:
        zone = "changeable"

    row = _SAGER_WIND_TABLE[zone][trend]
    return row.get(modifier, row[None])
