"""Weather platform for the Zambretti & Sager integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.weather import Forecast, WeatherEntity
from homeassistant.const import UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, VERSION, ZAMBRETTI_MAPPING
from .coordinator import ZambrettiSagerCoordinator

ZAMBRETTI_TO_CONDITION: dict[str, str] = {
    "settled_fine": "sunny",
    "fine_weather": "sunny",
    "fine_becoming_less_settled": "partlycloudy",
    "fairly_fine_showery_later": "rainy",
    "showery_becoming_more_unsettled": "rainy",
    "unsettled_rain_later": "rainy",
    "rain_at_times_worse_later": "rainy",
    "rain_at_times_becoming_very_unsettled": "rainy",
    "very_unsettled_rain": "rainy",
    "fine_possibly_showers": "partlycloudy",
    "fairly_fine_showers_likely": "rainy",
    "showery_bright_intervals": "cloudy",
    "changeable_some_rain": "rainy",
    "unsettled_rain_at_times": "rainy",
    "rain_at_frequent_intervals": "rainy",
    "stormy_much_rain": "lightning-rainy",
    "becoming_fine": "sunny",
    "fairly_fine_improving": "partlycloudy",
    "fairly_fine_possibly_showers_early": "partlycloudy",
    "showery_early_improving": "cloudy",
    "changeable_mending": "cloudy",
    "rather_unsettled_clearing_later": "cloudy",
    "unsettled_probably_improving": "cloudy",
    "unsettled_short_fine_intervals": "partlycloudy",
    "very_unsettled_finer_at_times": "rainy",
    "stormy_possibly_improving": "lightning-rainy",
    "stable": "clear-night",
}


def _zambretti_index(p_now: float, delta: float) -> int:
    if delta <= -1.6:
        z = round(127 - 0.12 * p_now)
    elif delta >= 1.6:
        z = round(185 - 0.16 * p_now)
    else:
        z = round(144 - 0.13 * p_now)
    return max(1, min(z, 32))


def _zambretti_state(p_now: float, p_ref: float) -> str | None:
    delta = p_now - p_ref
    return ZAMBRETTI_MAPPING.get(_zambretti_index(p_now, delta), "stable")


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Zambretti & Sager weather entity."""
    coordinator: ZambrettiSagerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ZambrettiWeather(coordinator)])


class ZambrettiWeather(CoordinatorEntity, WeatherEntity):
    """Weather entity that exposes Zambretti forecasts to HA's native weather card."""

    _attr_name = "Weather Station"
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_has_entity_name = True

    def __init__(self, coordinator: ZambrettiSagerCoordinator) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_weather"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name="Weather Station",
            manufacturer="Zambretti & Sager",
            model="Software Forecaster",
            sw_version=VERSION,
        )

    @property
    def data(self):
        return self.coordinator.data

    @property
    def condition(self) -> str | None:
        d = self.data
        if not d or not d.available or d.p_now is None:
            return None
        p_ref = d.p_3h if d.p_3h is not None else d.p_now
        state = _zambretti_state(d.p_now, p_ref)
        return ZAMBRETTI_TO_CONDITION.get(state) if state else None

    @property
    def native_temperature(self) -> float | None:
        return self.coordinator._get_temperature()

    @property
    def native_pressure(self) -> float | None:
        d = self.data
        if not d or d.p_now is None:
            return None
        return round(d.p_now, 1)

    @property
    def native_humidity(self) -> float | None:
        d = self.data
        if not d:
            return None
        return round(d.humidity, 1) if d.humidity is not None else None

    @property
    def native_wind_speed(self) -> float | None:
        d = self.data
        if not d:
            return None
        return round(d.wind_speed, 1) if d.wind_speed is not None else None

    @property
    def native_wind_bearing(self) -> float | None:
        d = self.data
        if not d:
            return None
        return round(d.wind_degrees, 1) if d.wind_degrees is not None else None

    @property
    def forecast(self) -> list[Forecast] | None:
        d = self.data
        if not d or not d.available or d.p_now is None:
            return None

        now = dt_util.utcnow()
        items: list[Forecast] = []

        p_ref_3h = d.p_3h if d.p_3h is not None else d.p_now

        for hours in (6, 12, 24):
            if hours == 6:
                delta = (d.p_now - p_ref_3h) * 2
                p_pred = d.p_now + delta
            elif hours == 12:
                p_ref = d.p_6h if d.p_6h is not None else p_ref_3h
                h = 6 if d.p_6h is not None else 3
                delta = (d.p_now - p_ref) / h * 12
                p_pred = d.p_now + delta
            else:
                p_ref = d.p_12h if d.p_12h is not None else (
                    d.p_6h if d.p_6h is not None else p_ref_3h
                )
                h = 12 if d.p_12h is not None else (6 if d.p_6h is not None else 3)
                delta = (d.p_now - p_ref) / h * 24
                p_pred = d.p_now + delta

            state = _zambretti_state(p_pred, delta)
            cond = ZAMBRETTI_TO_CONDITION.get(state) if state else None
            forecast_time = (now + timedelta(hours=hours)).isoformat()

            items.append(Forecast(
                datetime=forecast_time,
                condition=cond,
                native_temperature=self.native_temperature,
                native_temperature_unit=self.native_temperature_unit,
                native_pressure=round(p_pred, 1),
                native_pressure_unit=self.native_pressure_unit,
            ))

        return items
