"""Pressure utilities: parsing, sea-level correction, elevation lookup."""

from __future__ import annotations

import logging

from homeassistant.const import UnitOfPressure
from homeassistant.core import State
from homeassistant.util.unit_conversion import PressureConverter

from .elevation import _ELEVATION_CACHE, get_elevation

__all__ = [
    "_ELEVATION_CACHE",
    "calculate_sea_level_pressure",
    "get_elevation",
    "parse_pressure_hpa",
    "parse_pressure_hpa_from_history",
]

_LOGGER = logging.getLogger(__name__)

_INVALID_STATES = frozenset({"unknown", "unavailable", "none", ""})

_HPA_UNITS = frozenset(
    {
        UnitOfPressure.HPA,
        UnitOfPressure.MBAR,
        "hPa",
        "mbar",
        "mb",
    }
)


def calculate_sea_level_pressure(pressure, temperature, altitude):
    """Calculate sea-level pressure from absolute pressure using the barometric formula.

    Args:
        pressure: Absolute station pressure in hPa.
        temperature: Current temperature in °C.
        altitude: Station altitude in meters.

    Returns:
        Sea-level pressure in hPa.

    Uses the standard atmosphere approximation:
        P_sea = P_abs / (1 - (0.0065 * h) / (T + 0.0065 * h + 273.15))^5.257

    Falls back to a simple lapse rate correction if the formula yields
    an invalid factor (e.g., at very high altitudes).
    """
    if altitude is None or altitude == 0:
        return pressure

    factor = 1 - (0.0065 * altitude) / (temperature + 0.0065 * altitude + 273.15)

    if factor <= 0:
        # Fallback: approximate 1 hPa per 8.3 m
        return pressure + (altitude / 8.3)

    return pressure / (factor**5.257)


def _normalize_pressure_value(value: float, unit: str | None, entity_id: str) -> float:
    """Normalize a pressure reading to hPa based on its unit of measurement.

    Supports hPa, mbar, Pa, inHg, mmHg, bar, and psi.

    Args:
        value: Numeric pressure value.
        unit: Unit string from sensor attributes (e.g. "hPa", "mmHg", "inHg").
        entity_id: Sensor entity id for logging.

    Returns:
        Pressure in hPa.
    """
    if unit in _HPA_UNITS or unit is None:
        # If unit not specified but value > 2000, assume Pascals
        if unit is None and value > 2000:
            return value / 100
        return value

    u_lower = str(unit).lower().strip()
    if u_lower in ("pa", "pascal", "pascals"):
        return value / 100.0
    if u_lower in ("inhg", "in_hg"):
        return value * 33.863886666667
    if u_lower in ("mmhg", "mm_hg", "torr"):
        return value * 1.33322387415
    if u_lower in ("bar", "bars"):
        return value * 1000.0
    if u_lower in ("psi",):
        return value * 68.94757293168

    try:
        return PressureConverter.convert(value, unit, UnitOfPressure.HPA)
    except Exception:
        _LOGGER.warning(
            "Unknown pressure unit '%s' for %s, assuming hPa",
            unit,
            entity_id,
        )
        return value


def parse_pressure_hpa(state: State) -> float:
    """Read pressure from a sensor state and normalize to hPa.

    Args:
        state: HA State object from the pressure sensor.

    Returns:
        Pressure in hPa.

    Raises:
        ValueError: If state is invalid or cannot be parsed.
    """
    if state.state.lower() in _INVALID_STATES:
        raise ValueError(f"Sensor {state.entity_id} has invalid state: {state.state!r}")
    value = float(state.state)
    unit = state.attributes.get("unit_of_measurement")
    return _normalize_pressure_value(value, unit, state.entity_id)


def parse_pressure_hpa_from_history(history_state) -> float:
    """Read pressure from a recorder history entry and normalize to hPa.

    Handles three formats returned by HA history API:
    - Full State object (homeassistant.core.State)
    - Compact dict format (newer HA versions): {'state', 'lu', 'uom', ...}
    - LazyState or other objects with attributes

    Args:
        history_state: History entry from recorder.

    Returns:
        Pressure in hPa.

    Raises:
        ValueError: If state is invalid or cannot be parsed.
    """
    # Full State object from homeassistant.core
    if isinstance(history_state, State):
        return parse_pressure_hpa(history_state)

    # Compact dict format (minimal_response=true in newer HA)
    if isinstance(history_state, dict):
        state_value = history_state.get("state") or history_state.get("s")
        if state_value is None or str(state_value).lower() in _INVALID_STATES:
            raise ValueError(f"Invalid history pressure state: {state_value!r}")
        unit = (
            history_state.get("unit_of_measurement")
            or history_state.get("uom")
            or history_state.get("attributes", {}).get("unit_of_measurement")
        )
        entity_id = history_state.get("entity_id", "history")
        return _normalize_pressure_value(float(state_value), unit, entity_id)

    # LazyState or any object with attributes
    state_value = getattr(history_state, "state", None)
    if state_value is None or str(state_value).lower() in _INVALID_STATES:
        raise ValueError(f"Invalid history pressure state: {state_value!r}")

    unit = getattr(history_state, "attributes", {}).get("unit_of_measurement")
    entity_id = getattr(history_state, "entity_id", "history")
    return _normalize_pressure_value(float(state_value), unit, entity_id)
