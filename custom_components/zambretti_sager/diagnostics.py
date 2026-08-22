"""Diagnostics support for Zambretti & Sager integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_LATITUDE, CONF_LONGITUDE
from .coordinator import ZambrettiConfigEntry

TO_REDACT = {
    CONF_LATITUDE,
    CONF_LONGITUDE,
    "latitude",
    "longitude",
    "location",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ZambrettiConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    data = coordinator.data

    snapshot: dict[str, Any] = {}
    if data:
        snapshot = {
            "available": data.available,
            "p_now": data.p_now,
            "p_3h": data.p_3h,
            "p_6h": data.p_6h,
            "p_12h": data.p_12h,
            "delta_3h": data.delta_3h,
            "trend_label": data.trend_label,
            "zambretti_state": data.zambretti_state,
            "sager_state": data.sager_state,
            "zambretti_6h": data.zambretti_6h,
            "predicted_p_6h": data.predicted_p_6h,
            "zambretti_12h": data.zambretti_12h,
            "predicted_p_12h": data.predicted_p_12h,
            "zambretti_24h": data.zambretti_24h,
            "predicted_p_24h": data.predicted_p_24h,
            "precip_probability": data.precip_probability,
            "wind_degrees": data.wind_degrees,
            "wind_direction": data.wind_direction,
            "wind_speed": data.wind_speed,
            "humidity": data.humidity,
            "temperature": data.temperature,
            "altitude": data.altitude,
            "is_night": data.is_night,
            "last_updated": data.last_updated.isoformat() if data.last_updated else None,
        }

    return {
        "config_entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "domain": entry.domain,
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
            "pref_disable_new_entities": entry.pref_disable_new_entities,
            "pref_disable_polling": entry.pref_disable_polling,
        },
        "coordinator": {
            "pressure_sensor": coordinator.pressure_id,
            "wind_sensor": coordinator.wind_id,
            "wind_speed_sensor": coordinator.wind_speed_id,
            "temperature_sensor": coordinator.temp_id,
            "humidity_sensor": coordinator.humidity_id,
            "use_sea_level": coordinator.use_sea_level,
            "altitude": coordinator.altitude,
            "history_buffer_length": len(coordinator._history_buffer),
            "history_warmed": coordinator._history_warmed,
        },
        "forecast_data": snapshot,
    }
