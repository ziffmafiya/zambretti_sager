"""Unit tests for ForecastEngine domain service."""

from __future__ import annotations

import datetime

from custom_components.zambretti_sager.forecast_engine import (
    ForecastEngine,
    WeatherObservations,
)


def test_forecast_engine_stormy_conditions():
    """Test forecast engine under rapidly falling pressure and high humidity."""
    now = datetime.datetime(2026, 9, 21, 14, 0, tzinfo=datetime.UTC)
    obs = WeatherObservations(
        p_now=985.0,
        p_3h=992.0,  # delta = -7.0 hPa (falling rapidly)
        p_6h=998.0,
        p_12h=1005.0,
        wind_degrees=180.0,  # S
        wind_speed=12.5,
        humidity=95.0,
        temperature=12.0,
        altitude=50.0,
        is_night=False,
        timestamp=now,
    )

    data = ForecastEngine.compute(obs)

    assert data.available is True
    assert data.p_now == 985.0
    assert data.delta_3h == -7.0
    assert "Falling Fast" in data.trend_label
    assert data.wind_direction == "S"
    assert data.precip_probability >= 90
    assert data.zambretti_state in (
        "very_unsettled_rain",
        "rain_at_times_becoming_very_unsettled",
        "stormy_much_rain",
    )
    assert data.sager_state == "sager_unsettled_rain_likely"
    assert data.predicted_p_6h < data.p_now


def test_forecast_engine_fair_improving_conditions():
    """Test forecast engine under rising pressure and north wind."""
    now = datetime.datetime(2026, 9, 21, 14, 0, tzinfo=datetime.UTC)
    obs = WeatherObservations(
        p_now=1028.0,
        p_3h=1024.0,  # delta = +4.0 hPa (rising fast)
        p_6h=1020.0,
        p_12h=1015.0,
        wind_degrees=10.0,  # N
        wind_speed=2.0,
        humidity=35.0,
        temperature=20.0,
        altitude=100.0,
        is_night=True,
        timestamp=now,
    )

    data = ForecastEngine.compute(obs)

    assert data.available is True
    assert data.delta_3h == 4.0
    assert "Rising Fast" in data.trend_label
    assert data.wind_direction == "N"
    assert data.precip_probability <= 15
    assert data.is_night is True
    assert data.predicted_p_6h > data.p_now
    assert data.predicted_p_12h > data.predicted_p_6h
    assert data.predicted_p_24h > data.predicted_p_12h


def test_forecast_engine_missing_optional_data():
    """Test forecast engine resilience with minimal required observations."""
    now = datetime.datetime(2026, 9, 21, 14, 0, tzinfo=datetime.UTC)
    obs = WeatherObservations(
        p_now=1013.25,
        p_3h=1013.25,
        p_6h=None,
        p_12h=None,
        wind_degrees=None,
        wind_speed=None,
        humidity=None,
        timestamp=now,
    )

    data = ForecastEngine.compute(obs)

    assert data.available is True
    assert data.delta_3h == 0.0
    assert data.trend_label == "→ Steady"
    assert data.wind_direction is None
    assert data.wind_degrees is None
    assert data.wind_speed is None
    assert data.humidity is None
    assert data.precip_probability is not None
    assert data.predicted_p_6h == 1013.2
