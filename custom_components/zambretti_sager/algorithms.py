"""Algorithmic functions for Zambretti, Sager, and weather forecasting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# Zambretti algorithm mapping: pressure trend index (1–32) → translation key
# The original Zambretti algorithm has 32 forecast states grouped by
# pressure trend: Falling (1-9), Steady (10-19), Rising (20-32)
ZAMBRETTI_MAPPING: Final[dict[int, str]] = {
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
SAGER_TREND_RAPID: Final[float] = 1.4
SAGER_TREND_SLOW: Final[float] = 0.7

# 8-point wind compass directions
WIND_COMPASS: Final[tuple[str, ...]] = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")

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


def get_trend_label(delta_hpa: float) -> str:
    """Return human-readable trend label for attributes."""
    trend = classify_pressure_trend(delta_hpa)
    return {
        "rising_rapidly": "↑↑ Rising Fast",
        "rising_slowly": "↑ Rising",
        "steady": "→ Steady",
        "falling_slowly": "↓ Falling",
        "falling_rapidly": "↓↓ Falling Fast",
    }.get(trend, "→ Steady")


def calculate_zambretti_index(p_now: float, delta_hpa: float) -> int:
    """Calculate Zambretti index (1–32) from pressure and trend.

    The original Zambretti algorithm uses different formulas for
    falling, steady, and rising pressure trends.
    """
    if delta_hpa <= -1.6:  # Falling
        z = round(127 - 0.12 * p_now)
    elif delta_hpa >= 1.6:  # Rising
        z = round(185 - 0.16 * p_now)
    else:  # Steady
        z = round(144 - 0.13 * p_now)
    return max(1, min(z, 32))


def calculate_precipitation_probability(
    p_now: float, delta_hpa: float, humidity: float | None = None
) -> int:
    """Calculate precipitation probability percentage based on pressure, trend, and humidity."""
    if p_now < 1000:
        base_prob = 90
    elif p_now < 1005:
        base_prob = 70
    elif p_now < 1010:
        base_prob = 50
    elif p_now < 1015:
        base_prob = 30
    elif p_now < 1020:
        base_prob = 15
    else:
        base_prob = 5

    if delta_hpa < -3.0:
        trend_modifier = 30
    elif delta_hpa < -1.6:
        trend_modifier = 15
    elif delta_hpa > 3.0:
        trend_modifier = -30
    elif delta_hpa > 1.6:
        trend_modifier = -15
    else:
        trend_modifier = 0

    humidity_modifier = 0
    if humidity is not None:
        if humidity >= 90:
            humidity_modifier = 15
        elif humidity >= 80:
            humidity_modifier = 10
        elif humidity >= 70:
            humidity_modifier = 5
        elif humidity <= 30:
            humidity_modifier = -15
        elif humidity <= 40:
            humidity_modifier = -10

    return round(max(0, min(100, base_prob + trend_modifier + humidity_modifier)))


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


@dataclass(frozen=True)
class ExtrapolatedForecast:
    """Predicted pressure and forecast state for a future time horizon."""

    predicted_pressure: float
    forecast_state: str


def calculate_extrapolations(
    p_now: float,
    p_3h: float,
    p_6h: float | None,
    p_12h: float | None,
) -> dict[int, ExtrapolatedForecast]:
    """Calculate extrapolated pressure and Zambretti states for 6h, 12h, and 24h horizons.

    Args:
        p_now: Current sea-level pressure.
        p_3h: Pressure 3 hours ago.
        p_6h: Pressure 6 hours ago (if available).
        p_12h: Pressure 12 hours ago (if available).

    Returns:
        Dict mapping horizon in hours (6, 12, 24) to ExtrapolatedForecast.
    """
    # 6h extrapolation (trend over 3h extrapolated x2)
    delta_6h = (p_now - p_3h) * 2
    predicted_p_6h = round(p_now + delta_6h, 1)
    zambretti_6h = ZAMBRETTI_MAPPING.get(
        calculate_zambretti_index(predicted_p_6h, delta_6h), "stable"
    )

    # 12h extrapolation
    p_ref_12 = p_6h if p_6h is not None else p_3h
    h_12 = 6 if p_6h is not None else 3
    delta_12h = (p_now - p_ref_12) / h_12 * 12
    predicted_p_12h = round(p_now + delta_12h, 1)
    zambretti_12h = ZAMBRETTI_MAPPING.get(
        calculate_zambretti_index(predicted_p_12h, delta_12h), "stable"
    )

    # 24h extrapolation
    if p_12h is not None:
        p_ref_24 = p_12h
        h_24 = 12
    elif p_6h is not None:
        p_ref_24 = p_6h
        h_24 = 6
    else:
        p_ref_24 = p_3h
        h_24 = 3

    delta_24h = (p_now - p_ref_24) / h_24 * 24
    predicted_p_24h = round(p_now + delta_24h, 1)
    zambretti_24h = ZAMBRETTI_MAPPING.get(
        calculate_zambretti_index(predicted_p_24h, delta_24h), "stable"
    )

    return {
        6: ExtrapolatedForecast(predicted_p_6h, zambretti_6h),
        12: ExtrapolatedForecast(predicted_p_12h, zambretti_12h),
        24: ExtrapolatedForecast(predicted_p_24h, zambretti_24h),
    }
