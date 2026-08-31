"""Unit tests for sensor entities and weather platform."""

from __future__ import annotations

import datetime
from unittest.mock import MagicMock

import pytest

from custom_components.zambretti_sager.coordinator import ForecastData
from custom_components.zambretti_sager.sensor import (
    LastUpdateSensor,
    PrecipitationProbability,
    SagerSensor,
    ZambrettiForecast6h,
    ZambrettiForecast12h,
    ZambrettiForecast24h,
    ZambrettiSensor,
)
from custom_components.zambretti_sager.weather import ZambrettiWeather


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with ForecastData."""
    coordinator = MagicMock()
    coordinator.entry.entry_id = "test_entry_id"
    coordinator.pressure_id = "sensor.barometer"
    coordinator.wind_id = "sensor.wind"
    coordinator.altitude = 120.0

    coordinator.data = ForecastData(
        available=True,
        p_now=1016.4,
        p_3h=1014.2,
        p_6h=1012.0,
        p_12h=1008.5,
        wind_degrees=270.0,
        wind_direction="W",
        wind_speed=3.5,
        humidity=55.0,
        altitude=120.0,
        temperature=21.5,
        is_night=False,
        last_updated=datetime.datetime(2026, 8, 22, 16, 0, tzinfo=datetime.UTC),
        delta_3h=2.2,
        trend_label="↑ Rising",
        zambretti_state="settled_fine",
        sager_state="sager_fair_improving",
        zambretti_6h="fairly_fine_improving",
        predicted_p_6h=1020.8,
        zambretti_12h="fine_weather",
        predicted_p_12h=1025.2,
        zambretti_24h="settled_fine",
        predicted_p_24h=1032.2,
        precip_probability=10,
    )
    return coordinator


def test_zambretti_sensor(mock_coordinator):
    """Test ZambrettiSensor properties and attributes."""
    sensor = ZambrettiSensor(mock_coordinator)
    assert sensor.translation_key == "zambretti_forecast"
    assert sensor.unique_id == "test_entry_id_zambretti"
    assert sensor.native_value == "settled_fine"
    assert sensor.available is True

    attrs = sensor.extra_state_attributes
    assert attrs["pressure_sensor"] == "sensor.barometer"
    assert attrs["pressure_hpa"] == 1016.4
    assert attrs["pressure_3h_ago"] == 1014.2
    assert attrs["trend"] == "↑ Rising"
    assert attrs["wind_direction"] == "W"


def test_sager_sensor(mock_coordinator):
    """Test SagerSensor properties."""
    sensor = SagerSensor(mock_coordinator)
    assert sensor.translation_key == "sager_forecast"
    assert sensor.unique_id == "test_entry_id_sager"
    assert sensor.native_value == "sager_fair_improving"


def test_forecast_horizon_sensors(mock_coordinator):
    """Test 6h, 12h, and 24h Zambretti extrapolation sensors."""
    s6 = ZambrettiForecast6h(mock_coordinator)
    assert s6.translation_key == "zambretti_forecast_6h"
    assert s6.native_value == "fairly_fine_improving"
    assert s6.extra_state_attributes["predicted_pressure_hpa"] == 1020.8

    s12 = ZambrettiForecast12h(mock_coordinator)
    assert s12.translation_key == "zambretti_forecast_12h"
    assert s12.native_value == "fine_weather"
    assert s12.extra_state_attributes["predicted_pressure_hpa"] == 1025.2

    s24 = ZambrettiForecast24h(mock_coordinator)
    assert s24.translation_key == "zambretti_forecast_24h"
    assert s24.native_value == "settled_fine"
    assert s24.extra_state_attributes["predicted_pressure_hpa"] == 1032.2


def test_precipitation_probability_sensor(mock_coordinator):
    """Test PrecipitationProbability sensor."""
    sensor = PrecipitationProbability(mock_coordinator)
    assert sensor.translation_key == "precipitation_probability"
    assert sensor.native_value == 10


def test_last_update_sensor(mock_coordinator):
    """Test LastUpdateSensor properties and entity category."""
    sensor = LastUpdateSensor(mock_coordinator)
    assert sensor.translation_key == "last_update"
    assert sensor.available is True
    assert sensor.native_value == datetime.datetime(2026, 8, 22, 16, 0, tzinfo=datetime.UTC)
    assert sensor.force_update is True


def test_weather_entity(mock_coordinator):
    """Test ZambrettiWeather entity condition and forecast properties."""
    weather = ZambrettiWeather(mock_coordinator)
    assert weather.condition == "sunny"
    assert weather.native_temperature == 21.5
    assert weather.native_pressure == 1016.4
    assert weather.native_humidity == 55.0
    assert weather.native_wind_speed == 3.5
    assert weather.wind_bearing == 270.0

    forecast = weather.forecast
    assert forecast is not None
    assert len(forecast) == 3
    assert forecast[0]["condition"] is not None
    assert forecast[0]["native_temperature"] == 21.5
    assert forecast[0]["native_pressure"] == 1020.8
