"""Data coordinator for the Zambretti & Sager integration."""

from __future__ import annotations

import asyncio
import datetime
import logging
from dataclasses import dataclass, field

from homeassistant.config_entries import ConfigEntry
from homeassistant.components.recorder import get_instance, history
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_PRESSURE_SENSOR,
    CONF_TEMPERATURE_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_USE_SEA_LEVEL,
    CONF_WIND_SENSOR,
    CONF_WIND_SPEED_SENSOR,
    DOMAIN,
)
from .pressure_util import (
    calculate_sea_level_pressure,
    get_elevation,
    parse_pressure_hpa,
    parse_pressure_hpa_from_history,
)

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = datetime.timedelta(minutes=5)
HISTORY_HOURS = (3, 6, 12)


@dataclass
class ForecastData:
    """Снимок данных для расчёта прогнозов."""

    available: bool
    p_now: float | None = None
    p_3h: float | None = None
    p_6h: float | None = None
    p_12h: float | None = None
    wind_degrees: float | None = None
    wind_speed: float | None = None
    humidity: float | None = None
    altitude: float | None = None
    is_night: bool = False


class ZambrettiSagerCoordinator(DataUpdateCoordinator[ForecastData]):
    """Собирает давление и историю один раз на цикл обновления."""

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

        self.pressure_id = entry.options.get(
            CONF_PRESSURE_SENSOR, entry.data[CONF_PRESSURE_SENSOR]
        )
        self.wind_id = entry.options.get(CONF_WIND_SENSOR, entry.data.get(CONF_WIND_SENSOR))
        self.wind_speed_id = entry.options.get(CONF_WIND_SPEED_SENSOR, entry.data.get(CONF_WIND_SPEED_SENSOR))
        self.temp_id = entry.options.get(
            CONF_TEMPERATURE_SENSOR, entry.data.get(CONF_TEMPERATURE_SENSOR)
        )
        self.humidity_id = entry.options.get(
            CONF_HUMIDITY_SENSOR, entry.data.get(CONF_HUMIDITY_SENSOR)
        )
        self.use_sea_level = entry.options.get(
            CONF_USE_SEA_LEVEL, entry.data.get(CONF_USE_SEA_LEVEL, False)
        )
        self.latitude = entry.options.get(CONF_LATITUDE, entry.data.get(CONF_LATITUDE))
        self.longitude = entry.options.get(CONF_LONGITUDE, entry.data.get(CONF_LONGITUDE))

    def _update_sensor_ids(self) -> None:
        """Обновить идентификаторы сенсоров из конфигурации при reload."""
        entry = self.entry
        new_pressure_id = entry.options.get(
            CONF_PRESSURE_SENSOR, entry.data[CONF_PRESSURE_SENSOR]
        )
        if new_pressure_id != self._last_pressure_id:
            self._sea_level_warning_logged = False
            self._last_pressure_id = new_pressure_id

        self.pressure_id = new_pressure_id
        self.wind_id = entry.options.get(CONF_WIND_SENSOR, entry.data.get(CONF_WIND_SENSOR))
        self.wind_speed_id = entry.options.get(CONF_WIND_SPEED_SENSOR, entry.data.get(CONF_WIND_SPEED_SENSOR))
        self.temp_id = entry.options.get(
            CONF_TEMPERATURE_SENSOR, entry.data.get(CONF_TEMPERATURE_SENSOR)
        )
        self.humidity_id = entry.options.get(
            CONF_HUMIDITY_SENSOR, entry.data.get(CONF_HUMIDITY_SENSOR)
        )
        self.use_sea_level = entry.options.get(
            CONF_USE_SEA_LEVEL, entry.data.get(CONF_USE_SEA_LEVEL, False)
        )

    def _start_pressure_watcher(self) -> None:
        """Подписаться на изменения датчика давления."""
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
                self.hass.async_create_task(self.async_refresh())

        self._unsub_state_listener = async_track_state_change_event(
            self.hass, [self.pressure_id], _on_pressure_state_change
        )

    def _stop_pressure_watcher(self) -> None:
        """Unsubscribe from pressure sensor state change events."""
        if self._unsub_state_listener:
            self._unsub_state_listener()
            self._unsub_state_listener = None

    def _is_nighttime(self) -> bool:
        """Определить, сейчас ночь (через sun.sun)."""
        sun_state = self.hass.states.get("sun.sun")
        if sun_state and sun_state.attributes.get("elevation", 90) < 0:
            return True
        return False

    async def _async_update_data(self) -> ForecastData:
        """Прочитать текущее давление, историю и ветер."""
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

        p_now = self._correct_pressure(p_now_raw)
        history_raw = await self._fetch_history_pressures()
        wind = self._get_wind_direction()
        wind_speed = self._get_wind_speed()
        humidity = self._get_humidity()
        is_night = self._is_nighttime()
        _LOGGER.debug(
            "Coordinator update: p_now=%.1f p_3h=%s p_6h=%s p_12h=%s wind=%s wind_speed=%s humidity=%s night=%s",
            p_now,
            history_raw.get(3),
            history_raw.get(6),
            history_raw.get(12),
            wind,
            wind_speed,
            humidity,
            is_night,
        )

        return ForecastData(
            available=True,
            p_now=p_now,
            p_3h=self._correct_history_pressure(history_raw.get(3), p_now),
            p_6h=self._correct_history_pressure(history_raw.get(6), p_now),
            p_12h=self._correct_history_pressure(history_raw.get(12), p_now),
            wind_degrees=wind,
            wind_speed=wind_speed,
            humidity=humidity,
            altitude=self.altitude,
            is_night=is_night,
        )

    def _get_temperature(self) -> float:
        """Вернуть текущую температуру или стандартные 15 °C."""
        if not self.temp_id:
            return 15.0
        state = self.hass.states.get(self.temp_id)
        if not state or state.state in ("unknown", "unavailable"):
            return 15.0
        try:
            return float(state.state)
        except ValueError:
            return 15.0

    def _is_likely_sea_level_sensor(self) -> bool:
        """Определить, отдаёт ли датчик уже давление на уровне моря."""
        from .const import SEA_LEVEL_SENSOR_HINTS

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
        """Применить коррекцию на уровень моря."""
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
        return calculate_sea_level_pressure(
            raw_pressure, self._get_temperature(), self.altitude
        )

    def _correct_history_pressure(self, raw_pressure: float | None, fallback: float) -> float:
        """Скорректировать историческое давление или вернуть fallback."""
        if raw_pressure is None:
            return fallback
        return self._correct_pressure(raw_pressure)

    def _get_wind_direction(self) -> float | None:
        """Вернуть направление ветра в градусах или None."""
        if not self.wind_id:
            return None
        state = self.hass.states.get(self.wind_id)
        if not state or state.state in ("unknown", "unavailable"):
            return None
        try:
            return float(state.state)
        except ValueError:
            return None

    def _get_wind_speed(self) -> float | None:
        """Вернуть скорость ветра или None."""
        if not self.wind_speed_id:
            return None
        state = self.hass.states.get(self.wind_speed_id)
        if not state or state.state in ("unknown", "unavailable"):
            return None
        try:
            return float(state.state)
        except ValueError:
            return None

    def _get_humidity(self) -> float | None:
        """Вернуть относительную влажность в % или None."""
        if not self.humidity_id:
            return None
        state = self.hass.states.get(self.humidity_id)
        if not state or state.state in ("unknown", "unavailable"):
            return None
        try:
            return float(state.state)
        except ValueError:
            return None

    async def _fetch_history_pressures(self) -> dict[int, float | None]:
        """Параллельно получить давление 3, 6 и 12 часов назад."""
        now = dt_util.utcnow()
        results = await asyncio.gather(
            *(self._get_history_pressure(hours, now) for hours in HISTORY_HOURS)
        )
        return dict(zip(HISTORY_HOURS, results))

    async def _get_history_pressure(self, hours: int, now) -> float | None:
        """Получить давление N часов назад через recorder."""
        target_time = now - datetime.timedelta(hours=hours)
        window = datetime.timedelta(minutes=15)
        start_time = target_time - window
        end_time = target_time + window
        try:
            events = await asyncio.wait_for(
                get_instance(self.hass).async_add_executor_job(
                    history.get_significant_states,
                    self.hass,
                    start_time,
                    end_time,
                    [self.pressure_id],
                ),
                timeout=30.0,
            )
            if self.pressure_id in events and events[self.pressure_id]:
                best = min(
                    events[self.pressure_id],
                    key=lambda s: abs(
                        getattr(s, "last_changed", getattr(s, "last_updated", None)) - target_time
                        if hasattr(s, "last_changed")
                        else 0
                    ),
                )
                return parse_pressure_hpa_from_history(best)
        except Exception:
            _LOGGER.exception(
                "Error fetching pressure history for %s (%sh)",
                self.pressure_id,
                hours,
            )
        return None

async def async_create_coordinator(
    hass: HomeAssistant, entry: ConfigEntry
) -> ZambrettiSagerCoordinator:
    """Создать координатор и определить высоту при необходимости."""
    latitude = entry.options.get(CONF_LATITUDE, entry.data.get(CONF_LATITUDE))
    longitude = entry.options.get(CONF_LONGITUDE, entry.data.get(CONF_LONGITUDE))

    altitude = None
    if latitude is not None and longitude is not None:
        altitude = await get_elevation(hass, latitude, longitude)
        if altitude is not None:
            _LOGGER.info("Altitude for (%.6f, %.6f): %.1f m", latitude, longitude, altitude)
        else:
            _LOGGER.warning(
                "Could not determine altitude, sea level correction will use raw pressure"
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