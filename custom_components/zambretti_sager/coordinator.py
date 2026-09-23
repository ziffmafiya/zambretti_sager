"""Data coordinator for the Zambretti & Sager integration."""

from __future__ import annotations

import datetime
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_conversion import SpeedConverter, TemperatureConverter

from .const import (
    CONF_HUMIDITY_SENSOR,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_PRESSURE_SENSOR,
    CONF_TEMPERATURE_SENSOR,
    CONF_USE_SEA_LEVEL,
    CONF_WIND_SENSOR,
    CONF_WIND_SPEED_SENSOR,
    DOMAIN,
    SEA_LEVEL_SENSOR_HINTS,
)
from .elevation import async_resolve_elevation
from .forecast_engine import ForecastData, ForecastEngine, WeatherObservations
from .history import (
    PressureHistoryBuffer,
    async_get_history_pressures_batch_from_recorder,
    async_warm_history_buffer,
)
from .pressure_util import (
    calculate_sea_level_pressure,
    parse_pressure_hpa,
)

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = datetime.timedelta(minutes=5)
HISTORY_HOURS = (3, 6, 12)

type ZambrettiConfigEntry = ConfigEntry["ZambrettiSagerCoordinator"]

# Re-export for backward compatibility
__all__ = [
    "ForecastData",
    "ZambrettiConfigEntry",
    "ZambrettiSagerCoordinator",
    "async_create_coordinator",
]


class ZambrettiSagerCoordinator(DataUpdateCoordinator[ForecastData]):
    """Collects weather observations and coordinates forecast updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, altitude: float | None) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.entry = entry
        self.altitude = altitude
        self._sea_level_warning_logged = False
        self._unsub_state_listener = None
        self._last_pressure_id: str | None = None

        # In-memory rolling history buffer
        self._history_buffer = PressureHistoryBuffer()
        self._history_warmed = False

        # Load sensor entity IDs from config entry
        self._update_sensor_ids()

        # Register cleanup on unload
        entry.async_on_unload(self._stop_pressure_watcher)

    def _update_sensor_ids(self) -> None:
        """Update sensor entity IDs from config entry on reload."""
        entry = self.entry
        new_pressure_id = (
            entry.options.get(CONF_PRESSURE_SENSOR) or entry.data[CONF_PRESSURE_SENSOR]
        )
        if new_pressure_id != self._last_pressure_id:
            self._sea_level_warning_logged = False
            self._last_pressure_id = new_pressure_id
            self._history_buffer.clear()
            self._history_warmed = False

        self.pressure_id = new_pressure_id
        self.wind_id = entry.options.get(CONF_WIND_SENSOR) or entry.data.get(CONF_WIND_SENSOR)
        self.wind_speed_id = entry.options.get(CONF_WIND_SPEED_SENSOR) or entry.data.get(
            CONF_WIND_SPEED_SENSOR
        )
        self.temp_id = entry.options.get(CONF_TEMPERATURE_SENSOR) or entry.data.get(
            CONF_TEMPERATURE_SENSOR
        )
        self.humidity_id = entry.options.get(CONF_HUMIDITY_SENSOR) or entry.data.get(
            CONF_HUMIDITY_SENSOR
        )
        self.use_sea_level = (
            entry.options.get(CONF_USE_SEA_LEVEL)
            if CONF_USE_SEA_LEVEL in entry.options
            else entry.data.get(CONF_USE_SEA_LEVEL, False)
        )
        self.latitude = entry.options.get(CONF_LATITUDE) or entry.data.get(CONF_LATITUDE)
        self.longitude = entry.options.get(CONF_LONGITUDE) or entry.data.get(CONF_LONGITUDE)

    def _start_pressure_watcher(self) -> None:
        """Subscribe to pressure sensor state changes for immediate updates."""
        if self._unsub_state_listener:
            return

        @callback
        def _on_pressure_state_change(event) -> None:
            new_state = event.data.get("new_state")
            if new_state and new_state.state not in ("unknown", "unavailable", None):
                _LOGGER.debug(
                    "Pressure sensor %s became available (%s), triggering update",
                    self.pressure_id,
                    new_state.state,
                )
                self.hass.async_create_task(self.async_request_refresh())

        self._unsub_state_listener = async_track_state_change_event(
            self.hass, [self.pressure_id], _on_pressure_state_change
        )

    def _stop_pressure_watcher(self) -> None:
        """Unsubscribe from pressure sensor state change events."""
        if self._unsub_state_listener:
            self._unsub_state_listener()
            self._unsub_state_listener = None

    def _is_nighttime(self) -> bool:
        """Determine if it's currently night (using sun.sun elevation)."""
        sun_state = self.hass.states.get("sun.sun")
        return bool(sun_state and sun_state.attributes.get("elevation", 90) < 0)

    async def _async_update_data(self) -> ForecastData:
        """Fetch current pressure, history, and wind data, then compute forecast."""
        pressure_state = self.hass.states.get(self.pressure_id)
        if not pressure_state or pressure_state.state in ("unknown", "unavailable"):
            _LOGGER.debug(
                "Pressure sensor %s not ready yet (state: %s), waiting for state change",
                self.pressure_id,
                pressure_state.state if pressure_state else "not found",
            )
            self._start_pressure_watcher()
            return ForecastData(available=False)

        self._stop_pressure_watcher()

        try:
            p_now_raw = parse_pressure_hpa(pressure_state)
        except (TypeError, ValueError) as err:
            _LOGGER.error("Invalid pressure value for %s: %s", self.pressure_id, err)
            raise UpdateFailed(f"Invalid pressure state for {self.pressure_id}") from None

        # Apply sea-level correction if enabled
        p_now = self._correct_pressure(p_now_raw)
        temperature = self._get_temperature()
        now_dt = dt_util.utcnow()

        # Warm history buffer on first run with a single recorder query
        if not self._history_warmed:
            await async_warm_history_buffer(
                self.hass,
                self.pressure_id,
                self._history_buffer,
                hours=13,
                pressure_corrector=self._correct_pressure,
            )
            self._history_warmed = True

        # Append current reading and prune buffer
        self._history_buffer.append(now_dt, p_now)

        history_raw = await self._fetch_history_pressures(now_dt)
        wind = self._get_wind_direction()
        wind_speed = self._get_wind_speed()
        humidity = self._get_humidity()
        is_night = self._is_nighttime()

        # Historical pressures
        p_3h = self._correct_history_pressure(history_raw.get(3), p_now)
        p_6h = self._correct_history_pressure(history_raw.get(6), p_3h)
        p_12h = self._correct_history_pressure(history_raw.get(12), p_6h)

        observations = WeatherObservations(
            p_now=p_now,
            p_3h=p_3h,
            p_6h=p_6h,
            p_12h=p_12h,
            wind_degrees=wind,
            wind_speed=wind_speed,
            humidity=humidity,
            temperature=temperature,
            altitude=self.altitude,
            is_night=is_night,
            timestamp=now_dt,
        )

        forecast_data = ForecastEngine.compute(observations)

        _LOGGER.debug(
            "Coordinator update: p_now=%.1f delta_3h=%.2f zambretti=%s sager=%s night=%s (buffer: %d pts)",
            forecast_data.p_now or 0.0,
            forecast_data.delta_3h or 0.0,
            forecast_data.zambretti_state,
            forecast_data.sager_state,
            forecast_data.is_night,
            len(self._history_buffer),
        )

        return forecast_data

    def _get_temperature(self) -> float:
        """Return current temperature in °C using TemperatureConverter or fallback."""
        if not self.temp_id:
            return 15.0
        state = self.hass.states.get(self.temp_id)
        if not state or state.state in ("unknown", "unavailable"):
            return 15.0
        try:
            raw_val = float(state.state)
        except (ValueError, TypeError):
            return 15.0

        unit = state.attributes.get("unit_of_measurement")
        if unit and isinstance(unit, str):
            try:
                return float(TemperatureConverter.convert(raw_val, unit, UnitOfTemperature.CELSIUS))
            except Exception:
                unit_clean = unit.upper().replace("°", "").strip()
                if unit_clean == "F":
                    return (raw_val - 32.0) * 5.0 / 9.0
                if unit_clean == "K":
                    return raw_val - 273.15

        return raw_val

    def _is_likely_sea_level_sensor(self) -> bool:
        """Check if the pressure sensor already reports sea-level pressure (MSLP/QNH)."""
        state = self.hass.states.get(self.pressure_id)
        if not state:
            return False
        entity_id = self.pressure_id.lower()
        if any(hint in entity_id for hint in SEA_LEVEL_SENSOR_HINTS):
            return True
        for key in ("pressure_type", "sensor_type", "type"):
            value = str(state.attributes.get(key, "")).lower()
            if any(word in value for word in ("sea", "relative", "mslp")):
                return True
        return False

    def _correct_pressure(self, raw_pressure: float) -> float:
        """Apply sea-level pressure correction if enabled and sensor is absolute."""
        if not self.use_sea_level or self.altitude is None:
            return raw_pressure
        if self._is_likely_sea_level_sensor():
            if not self._sea_level_warning_logged:
                _LOGGER.warning(
                    "Pressure sensor %s appears to report sea level pressure; "
                    "skipping altitude correction to avoid double conversion",
                    self.pressure_id,
                )
                self._sea_level_warning_logged = True
            return raw_pressure
        return calculate_sea_level_pressure(raw_pressure, self._get_temperature(), self.altitude)

    def _correct_history_pressure(self, raw_pressure: float | None, fallback: float) -> float:
        """Correct historical pressure reading, or return fallback if unavailable."""
        if raw_pressure is None:
            return fallback
        return self._correct_pressure(raw_pressure)

    def _get_wind_direction(self) -> float | None:
        """Return wind direction in degrees or None."""
        if not self.wind_id:
            return None
        state = self.hass.states.get(self.wind_id)
        if not state or state.state in ("unknown", "unavailable"):
            return None

        # Check numeric state first
        try:
            return float(state.state)
        except (ValueError, TypeError):
            pass

        # Try attributes for numeric bearing/direction
        for attr in ("wind_bearing", "wind_degrees", "bearing", "degrees"):
            val = state.attributes.get(attr)
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    pass

        # Try converting compass string state (e.g. "N", "NE", "SW", etc.)
        compass_map = {
            "N": 0.0,
            "NNE": 22.5,
            "NE": 45.0,
            "ENE": 67.5,
            "E": 90.0,
            "ESE": 112.5,
            "SE": 135.0,
            "SSE": 157.5,
            "S": 180.0,
            "SSW": 202.5,
            "SW": 225.0,
            "WSW": 247.5,
            "W": 270.0,
            "WNW": 292.5,
            "NW": 315.0,
            "NNW": 337.5,
        }
        state_str = str(state.state).upper().strip()
        return compass_map.get(state_str)

    def _get_wind_speed(self) -> float | None:
        """Return wind speed in m/s using SpeedConverter or fallback."""
        sensor_id = self.wind_speed_id or self.wind_id
        if not sensor_id:
            return None
        state = self.hass.states.get(sensor_id)
        if not state or state.state in ("unknown", "unavailable"):
            return None

        raw_val: float | None = None
        try:
            raw_val = float(state.state)
        except (ValueError, TypeError):
            for attr in ("wind_speed", "speed"):
                val = state.attributes.get(attr)
                if val is not None:
                    try:
                        raw_val = float(val)
                        break
                    except (ValueError, TypeError):
                        pass

        if raw_val is None:
            return None

        unit = state.attributes.get("unit_of_measurement")
        if unit and isinstance(unit, str):
            try:
                return float(SpeedConverter.convert(raw_val, unit, UnitOfSpeed.METERS_PER_SECOND))
            except Exception:
                unit_clean = unit.lower().strip()
                if unit_clean in ("km/h", "kmh"):
                    return raw_val / 3.6
                if unit_clean in ("mph", "mi/h"):
                    return raw_val * 0.44704
                if unit_clean in ("kn", "kts", "knot", "knots"):
                    return raw_val * 0.514444
                if unit_clean in ("ft/s", "fps"):
                    return raw_val * 0.3048

        return raw_val

    def _get_humidity(self) -> float | None:
        """Return relative humidity in percent or None."""
        if not self.humidity_id:
            return None
        state = self.hass.states.get(self.humidity_id)
        if not state or state.state in ("unknown", "unavailable"):
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    async def _fetch_history_pressures(
        self, now: datetime.datetime | None = None
    ) -> dict[int, float | None]:
        """Fetch pressure at 3, 6, and 12 hours ago (memory buffer first, single batch fallback to recorder)."""
        if now is None:
            now = dt_util.utcnow()
        results: dict[int, float | None] = {}
        missing_hours: list[int] = []

        for hours in HISTORY_HOURS:
            p = self._history_buffer.get_pressure_at(now - datetime.timedelta(hours=hours))
            results[hours] = p
            if p is None:
                missing_hours.append(hours)

        # Batch fallback to recorder if points are missing and buffer wasn't warmed
        if missing_hours and not self._history_warmed and self.pressure_id:
            batch_results = await async_get_history_pressures_batch_from_recorder(
                self.hass,
                self.pressure_id,
                missing_hours,
                now,
                pressure_corrector=self._correct_pressure if self.use_sea_level else None,
                buffer=self._history_buffer,
            )
            for h, p in batch_results.items():
                if p is not None:
                    results[h] = p
            self._history_warmed = True

        return results


async def async_create_coordinator(
    hass: HomeAssistant, entry: ZambrettiConfigEntry
) -> ZambrettiSagerCoordinator:
    """Create coordinator and resolve altitude using Local-First strategy."""
    latitude = entry.options.get(CONF_LATITUDE, entry.data.get(CONF_LATITUDE))
    longitude = entry.options.get(CONF_LONGITUDE, entry.data.get(CONF_LONGITUDE))

    altitude = await async_resolve_elevation(
        hass,
        latitude=latitude,
        longitude=longitude,
        configured_elevation=getattr(getattr(hass, "config", None), "elevation", None),
    )

    coordinator = ZambrettiSagerCoordinator(hass, entry, altitude)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        _LOGGER.warning(
            "Initial data fetch failed for %s, will retry automatically",
            entry.title,
        )
    return coordinator
