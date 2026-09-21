"""Forecast engine: pure domain service for computing weather forecasts."""

from __future__ import annotations

from dataclasses import dataclass
import datetime

from .algorithms import (
    ZAMBRETTI_MAPPING,
    calculate_extrapolations,
    calculate_precipitation_probability,
    calculate_sager_forecast,
    calculate_zambretti_index,
    get_trend_label,
    wind_degrees_to_compass,
)


@dataclass
class ForecastData:
    """Snapshot of data and computed forecasts."""

    available: bool
    p_now: float | None = None  # Current sea-level pressure (hPa)
    p_3h: float | None = None  # Pressure 3 hours ago
    p_6h: float | None = None  # Pressure 6 hours ago
    p_12h: float | None = None  # Pressure 12 hours ago
    wind_degrees: float | None = None  # Wind direction in degrees
    wind_direction: str | None = None  # Wind compass (e.g. "NW")
    wind_speed: float | None = None  # Wind speed (m/s)
    humidity: float | None = None  # Relative humidity (%)
    altitude: float | None = None  # Station altitude (meters)
    temperature: float = 15.0  # Current temperature (°C)
    is_night: bool = False  # True if sun is below horizon
    last_updated: datetime.datetime | None = None  # UTC timestamp of this snapshot

    # Pre-calculated forecast fields
    delta_3h: float | None = None  # Pressure delta over 3h
    trend_label: str = "→ Steady"  # Trend string for attributes
    zambretti_state: str | None = None  # Current Zambretti forecast translation key
    sager_state: str | None = None  # Current Sager forecast translation key
    zambretti_6h: str | None = None  # 6h Zambretti forecast translation key
    predicted_p_6h: float | None = None  # Predicted pressure in 6h
    zambretti_12h: str | None = None  # 12h Zambretti forecast translation key
    predicted_p_12h: float | None = None  # Predicted pressure in 12h
    zambretti_24h: str | None = None  # 24h Zambretti forecast translation key
    predicted_p_24h: float | None = None  # Predicted pressure in 24h
    precip_probability: int | None = None  # Precipitation probability 0-100%


@dataclass(frozen=True)
class WeatherObservations:
    """Snapshot of raw weather observations to evaluate."""

    p_now: float
    p_3h: float
    p_6h: float | None = None
    p_12h: float | None = None
    wind_degrees: float | None = None
    wind_speed: float | None = None
    humidity: float | None = None
    temperature: float = 15.0
    altitude: float | None = None
    is_night: bool = False
    timestamp: datetime.datetime | None = None


class ForecastEngine:
    """Pure domain service for generating forecasts from barometric trends."""

    @staticmethod
    def compute(obs: WeatherObservations) -> ForecastData:
        """Calculate forecasts, trends, extrapolations, and probabilities."""
        delta_3h = round(obs.p_now - obs.p_3h, 2)
        trend_label = get_trend_label(delta_3h)

        zambretti_index = calculate_zambretti_index(obs.p_now, delta_3h)
        zambretti_state = ZAMBRETTI_MAPPING.get(zambretti_index, "stable")

        sager_state = calculate_sager_forecast(obs.p_now, delta_3h, obs.wind_degrees)
        wind_direction = wind_degrees_to_compass(obs.wind_degrees)

        extrapolations = calculate_extrapolations(obs.p_now, obs.p_3h, obs.p_6h, obs.p_12h)
        precip_prob = calculate_precipitation_probability(obs.p_now, delta_3h, obs.humidity)

        f6 = extrapolations[6]
        f12 = extrapolations[12]
        f24 = extrapolations[24]

        return ForecastData(
            available=True,
            p_now=round(obs.p_now, 1),
            p_3h=round(obs.p_3h, 1),
            p_6h=round(obs.p_6h, 1) if obs.p_6h is not None else round(obs.p_3h, 1),
            p_12h=round(obs.p_12h, 1) if obs.p_12h is not None else round(obs.p_3h, 1),
            wind_degrees=round(obs.wind_degrees, 1) if obs.wind_degrees is not None else None,
            wind_direction=wind_direction,
            wind_speed=round(obs.wind_speed, 1) if obs.wind_speed is not None else None,
            humidity=round(obs.humidity, 1) if obs.humidity is not None else None,
            altitude=round(obs.altitude, 1) if obs.altitude is not None else None,
            temperature=round(obs.temperature, 1),
            is_night=obs.is_night,
            last_updated=obs.timestamp,
            delta_3h=delta_3h,
            trend_label=trend_label,
            zambretti_state=zambretti_state,
            sager_state=sager_state,
            zambretti_6h=f6.forecast_state,
            predicted_p_6h=f6.predicted_pressure,
            zambretti_12h=f12.forecast_state,
            predicted_p_12h=f12.predicted_pressure,
            zambretti_24h=f24.forecast_state,
            predicted_p_24h=f24.predicted_pressure,
            precip_probability=precip_prob,
        )
