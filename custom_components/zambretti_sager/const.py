"""Constants for the Zambretti & Sager integration."""

from typing import Final

DOMAIN = "zambretti_sager"

VERSION = "1.9.71"

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


def calculate_sager_forecast(
    pressure_hpa: float,
    delta_hpa: float,
    wind_degrees: float | None = None,
) -> str:
    """Calculate simplified Sager forecast (returns translation key).

    The classic Sager algorithm uses pressure, 3-hour trend, and wind direction.
    This implementation covers the pressure/trend logic; wind direction could
    be added for more granularity.

    Args:
        pressure_hpa: Current pressure (preferably sea-level corrected) in hPa.
        delta_hpa: Pressure change over ~3 hours.
        wind_degrees: Optional wind direction in degrees.

    Returns:
        Translation key for the Sager forecast state.
    """
    trend = classify_pressure_trend(delta_hpa)

    if pressure_hpa > 1020:
        if trend in ("rising_rapidly", "rising_slowly"):
            return "sager_fair_improving"
        elif trend in ("falling_rapidly", "falling_slowly"):
            return "sager_fair_tending_to_deteriorate"
        else:
            return "sager_fair_no_change"
    elif pressure_hpa < 1005:
        if trend in ("falling_rapidly", "falling_slowly"):
            return "sager_unsettled_rain_likely"
        elif trend in ("rising_rapidly", "rising_slowly"):
            return "sager_unsettled_probably_improving"
        else:
            return "sager_unsettled_rain_at_times"
    elif trend == "rising_rapidly":
        return "sager_changeable_becoming_fairer"
    elif trend == "falling_rapidly":
        return "sager_changeable_becoming_more_unsettled"
    elif trend == "rising_slowly":
        return "sager_variable_slowly_improving"
    elif trend == "falling_slowly":
        return "sager_variable_slowly_deteriorating"
    else:
        return "sager_variable_some_change"
