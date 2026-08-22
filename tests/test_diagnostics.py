"""Unit tests for Zambretti & Sager diagnostics platform."""

from __future__ import annotations

import datetime
from unittest.mock import MagicMock
import pytest

from custom_components.zambretti_sager.coordinator import ForecastData
from custom_components.zambretti_sager.diagnostics import async_get_config_entry_diagnostics


@pytest.mark.asyncio
async def test_diagnostics_redaction():
    """Test diagnostics export and coordinate redaction."""
    hass = MagicMock()

    entry = MagicMock()
    entry.entry_id = "test_entry_123"
    entry.version = 1
    entry.domain = "zambretti_sager"
    entry.title = "Weather Station"
    entry.data = {
        "pressure_sensor": "sensor.barometer",
        "latitude": 55.75,
        "longitude": 37.61,
    }
    entry.options = {
        "location": {"latitude": 55.75, "longitude": 37.61},
    }
    entry.pref_disable_new_entities = False
    entry.pref_disable_polling = False

    coordinator = MagicMock()
    coordinator.pressure_id = "sensor.barometer"
    coordinator.wind_id = None
    coordinator.wind_speed_id = None
    coordinator.temp_id = None
    coordinator.humidity_id = None
    coordinator.use_sea_level = True
    coordinator.altitude = 150.0
    coordinator._history_buffer = [(datetime.datetime.now(), 1013.25)]
    coordinator._history_warmed = True

    coordinator.data = ForecastData(
        available=True,
        p_now=1013.2,
        p_3h=1012.0,
        p_6h=1010.0,
        p_12h=1008.0,
        delta_3h=1.2,
        trend_label="↑ Rising",
        zambretti_state="settled_fine",
        sager_state="sager_fair_improving",
        last_updated=datetime.datetime(2026, 8, 22, 12, 0, tzinfo=datetime.timezone.utc),
    )

    entry.runtime_data = coordinator

    # Mock async_redact_data to simulate HA diagnostics behavior
    import custom_components.zambretti_sager.diagnostics as diag_module
    diag_module.async_redact_data = lambda data, to_redact: {
        k: "**REDACTED**" if k in to_redact else v for k, v in data.items()
    }

    diag = await async_get_config_entry_diagnostics(hass, entry)

    assert "config_entry" in diag
    assert "coordinator" in diag
    assert "forecast_data" in diag

    assert diag["config_entry"]["data"]["latitude"] == "**REDACTED**"
    assert diag["config_entry"]["data"]["longitude"] == "**REDACTED**"
    assert diag["config_entry"]["data"]["pressure_sensor"] == "sensor.barometer"
    assert diag["coordinator"]["use_sea_level"] is True
    assert diag["forecast_data"]["zambretti_state"] == "settled_fine"
