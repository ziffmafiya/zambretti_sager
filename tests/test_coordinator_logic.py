"""Unit tests for coordinator rolling buffer and data structures."""

from __future__ import annotations

from collections import deque
import datetime
from unittest.mock import MagicMock

import pytest

from custom_components.zambretti_sager.coordinator import (
    ForecastData,
    ZambrettiSagerCoordinator,
)


def test_forecast_data_structure():
    """Test ForecastData structure and default fields."""
    fd = ForecastData(
        available=True,
        p_now=1015.5,
        p_3h=1013.5,
        p_6h=1011.0,
        p_12h=1008.0,
        wind_degrees=180.0,
        wind_direction="S",
        wind_speed=5.2,
        humidity=65.0,
        altitude=150.0,
        temperature=18.5,
        is_night=False,
        last_updated=datetime.datetime(2026, 8, 22, 12, 0, tzinfo=datetime.UTC),
        delta_3h=2.0,
        trend_label="↑ Rising",
        zambretti_state="settled_fine",
        sager_state="sager_fair_improving",
        zambretti_6h="fairly_fine_improving",
        predicted_p_6h=1019.5,
        precip_probability=15,
    )

    assert fd.available is True
    assert fd.p_now == 1015.5
    assert fd.delta_3h == 2.0
    assert fd.trend_label == "↑ Rising"
    assert fd.zambretti_state == "settled_fine"
    assert fd.precip_probability == 15


def test_buffer_lookup_logic():
    """Test in-memory rolling buffer pressure lookup by delta hours."""
    now = datetime.datetime(2026, 8, 22, 12, 0, tzinfo=datetime.UTC)
    t_3h = now - datetime.timedelta(hours=3)
    t_6h = now - datetime.timedelta(hours=6)
    t_12h = now - datetime.timedelta(hours=12)

    buffer: deque[tuple[datetime.datetime, float]] = deque(
        [
            (t_12h, 1005.0),
            (t_6h, 1010.0),
            (t_3h + datetime.timedelta(minutes=5), 1015.0),  # slightly offset but within 45m
            (now, 1020.0),
        ]
    )

    # Lookup helper simulating _get_buffer_pressure
    def lookup(hours: int) -> float | None:
        target = now - datetime.timedelta(hours=hours)
        best = None
        best_diff = datetime.timedelta(minutes=45)
        for dt, p in buffer:
            diff = abs(dt - target)
            if diff <= best_diff:
                best_diff = diff
                best = p
        return best

    assert lookup(3) == 1015.0
    assert lookup(6) == 1010.0
    assert lookup(12) == 1005.0
    assert lookup(20) is None  # outside tolerance


def test_coordinator_temperature_conversion():
    """Test coordinator temperature unit conversion with SpeedConverter/TemperatureConverter."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test"
    mock_entry.data = {"pressure_sensor": "sensor.p"}
    mock_entry.options = {}

    coord = ZambrettiSagerCoordinator(mock_hass, mock_entry, altitude=100.0)
    coord.temp_id = "sensor.t"

    # Celsius
    mock_hass.states.get.return_value = MagicMock(
        state="20.0", attributes={"unit_of_measurement": "°C"}
    )
    assert pytest.approx(coord._get_temperature()) == 20.0

    # Fahrenheit (68°F = 20°C)
    mock_hass.states.get.return_value = MagicMock(
        state="68.0", attributes={"unit_of_measurement": "°F"}
    )
    assert pytest.approx(coord._get_temperature()) == 20.0

    # Kelvin (293.15 K = 20°C)
    mock_hass.states.get.return_value = MagicMock(
        state="293.15", attributes={"unit_of_measurement": "K"}
    )
    assert pytest.approx(coord._get_temperature(), abs=0.1) == 20.0

    # Missing sensor falls back to standard 15.0°C
    coord.temp_id = None
    assert coord._get_temperature() == 15.0


def test_coordinator_wind_speed_conversion():
    """Test coordinator wind speed conversion to m/s."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test"
    mock_entry.data = {"pressure_sensor": "sensor.p"}
    mock_entry.options = {}

    coord = ZambrettiSagerCoordinator(mock_hass, mock_entry, altitude=100.0)
    coord.wind_speed_id = "sensor.wind_speed"

    # km/h (36 km/h = 10 m/s)
    mock_hass.states.get.return_value = MagicMock(
        state="36.0", attributes={"unit_of_measurement": "km/h"}
    )
    assert pytest.approx(coord._get_wind_speed()) == 10.0

    # knots (10 knots ~ 5.14 m/s)
    mock_hass.states.get.return_value = MagicMock(
        state="10.0", attributes={"unit_of_measurement": "kn"}
    )
    assert pytest.approx(coord._get_wind_speed(), abs=0.01) == 5.14


def test_coordinator_sea_level_detection():
    """Test detection of sensors that already report sea level pressure."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test"
    mock_entry.data = {"pressure_sensor": "sensor.bme280_sealevel_pressure"}
    mock_entry.options = {}

    coord = ZambrettiSagerCoordinator(mock_hass, mock_entry, altitude=100.0)
    mock_hass.states.get.return_value = MagicMock(attributes={})

    assert coord._is_likely_sea_level_sensor() is True

    # Absolute sensor
    coord.pressure_id = "sensor.bme280_pressure"
    mock_hass.states.get.return_value = MagicMock(attributes={"pressure_type": "absolute"})
    assert coord._is_likely_sea_level_sensor() is False


def test_coordinator_wind_direction():
    """Test coordinator wind direction resolution from state and attributes."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test"
    mock_entry.data = {"pressure_sensor": "sensor.p"}
    mock_entry.options = {}

    coord = ZambrettiSagerCoordinator(mock_hass, mock_entry, altitude=100.0)
    coord.wind_id = "sensor.wind"

    # Numeric state
    mock_hass.states.get.return_value = MagicMock(state="180.0", attributes={})
    assert coord._get_wind_direction() == 180.0

    # Compass string state ("NW" -> 315.0)
    mock_hass.states.get.return_value = MagicMock(state="NW", attributes={})
    assert coord._get_wind_direction() == 315.0

    # Attribute wind_bearing when state is non-numeric string
    mock_hass.states.get.return_value = MagicMock(state="custom", attributes={"wind_bearing": 90.0})
    assert coord._get_wind_direction() == 90.0

    # Unknown state returns None
    mock_hass.states.get.return_value = MagicMock(state="unknown", attributes={"wind_bearing": 90.0})
    assert coord._get_wind_direction() is None

    # Missing sensor
    coord.wind_id = None
    assert coord._get_wind_direction() is None


def test_coordinator_nighttime():
    """Test day/night detection via sun.sun elevation."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test"
    mock_entry.data = {"pressure_sensor": "sensor.p"}
    mock_entry.options = {}

    coord = ZambrettiSagerCoordinator(mock_hass, mock_entry, altitude=100.0)

    # Night (sun below horizon)
    mock_hass.states.get.return_value = MagicMock(attributes={"elevation": -5.0})
    assert coord._is_nighttime() is True

    # Day (sun above horizon)
    mock_hass.states.get.return_value = MagicMock(attributes={"elevation": 25.0})
    assert coord._is_nighttime() is False

    # Missing sun entity defaults to False
    mock_hass.states.get.return_value = None
    assert coord._is_nighttime() is False


def test_coordinator_humidity():
    """Test humidity extraction."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test"
    mock_entry.data = {"pressure_sensor": "sensor.p"}
    mock_entry.options = {}

    coord = ZambrettiSagerCoordinator(mock_hass, mock_entry, altitude=100.0)
    coord.humidity_id = "sensor.h"

    mock_hass.states.get.return_value = MagicMock(state="65.5")
    assert coord._get_humidity() == 65.5

    mock_hass.states.get.return_value = MagicMock(state="invalid")
    assert coord._get_humidity() is None

    coord.humidity_id = None
    assert coord._get_humidity() is None


@pytest.mark.asyncio
async def test_coordinator_async_update_data_unavailable():
    """Test coordinator handles unavailable pressure sensor gracefully."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test"
    mock_entry.data = {"pressure_sensor": "sensor.pressure"}
    mock_entry.options = {}

    coord = ZambrettiSagerCoordinator(mock_hass, mock_entry, altitude=100.0)

    # Sensor unavailable
    mock_hass.states.get.return_value = MagicMock(state="unavailable")
    data = await coord._async_update_data()

    assert data.available is False
    assert coord._unsub_state_listener is not None


@pytest.mark.asyncio
async def test_coordinator_async_update_data_success():
    """Test successful coordinator update cycle."""
    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test"
    mock_entry.data = {"pressure_sensor": "sensor.pressure", "use_sea_level_correction": True}
    mock_entry.options = {}

    coord = ZambrettiSagerCoordinator(mock_hass, mock_entry, altitude=100.0)
    coord.temp_id = None
    coord.wind_id = None
    coord.humidity_id = None
    coord._history_warmed = True  # skip recorder

    # Populate buffer with 3h ago reading (1010 hPa)
    now = datetime.datetime.now(datetime.UTC)
    coord._history_buffer.append(now - datetime.timedelta(hours=3), 1010.0)

    # Current pressure reading: 1013.25 hPa
    pressure_state = MagicMock(
        entity_id="sensor.pressure",
        state="1013.25",
        attributes={"unit_of_measurement": "hPa"},
    )

    def mock_states_get(entity_id):
        if entity_id == "sensor.pressure":
            return pressure_state
        return None

    mock_hass.states.get.side_effect = mock_states_get

    data = await coord._async_update_data()

    assert data.available is True
    assert data.p_now is not None
    assert data.p_3h is not None
    assert data.delta_3h is not None
    assert data.zambretti_state is not None
    assert data.sager_state is not None


@pytest.mark.asyncio
async def test_coordinator_fetch_history_pressures_batch_fallback():
    """Test coordinator falls back to single batch recorder query when buffer is empty."""
    from unittest.mock import AsyncMock, patch

    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.entry_id = "test"
    mock_entry.data = {"pressure_sensor": "sensor.pressure"}
    mock_entry.options = {}

    coord = ZambrettiSagerCoordinator(mock_hass, mock_entry, altitude=100.0)
    coord._history_warmed = False

    now = datetime.datetime(2026, 9, 21, 14, 0, tzinfo=datetime.UTC)
    mock_batch = AsyncMock(return_value={3: 1010.0, 6: 1008.0, 12: 1005.0})

    with patch(
        "custom_components.zambretti_sager.coordinator.async_get_history_pressures_batch_from_recorder",
        mock_batch,
    ):
        res = await coord._fetch_history_pressures(now)

    assert res == {3: 1010.0, 6: 1008.0, 12: 1005.0}
    assert mock_batch.call_count == 1
    # Check that missing_hours (3, 6, 12) were passed in a single batch
    call_args = mock_batch.call_args[0]
    assert call_args[2] == [3, 6, 12]
    assert coord._history_warmed is True



