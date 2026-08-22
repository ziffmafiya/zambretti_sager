"""Sensor platform for the Zambretti & Sager integration."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, VERSION
from .coordinator import ForecastData, ZambrettiConfigEntry, ZambrettiSagerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZambrettiConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Zambretti & Sager sensors."""
    coordinator = entry.runtime_data

    async_add_entities([
        ZambrettiSensor(coordinator),
        SagerSensor(coordinator),
        ZambrettiForecast6h(coordinator),
        ZambrettiForecast12h(coordinator),
        ZambrettiForecast24h(coordinator),
        PrecipitationProbability(coordinator),
        LastUpdateSensor(coordinator),
    ])


class WeatherSensorBase(CoordinatorEntity[ZambrettiSagerCoordinator], SensorEntity):
    """Base class for all forecast sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ZambrettiSagerCoordinator) -> None:
        """Initialize the sensor and set shared device info."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name="Weather Station",
            manufacturer="Zambretti & Sager",
            model="Software Forecaster",
            sw_version=VERSION,
        )

    @property
    def data(self) -> ForecastData | None:
        """Return the latest forecast data snapshot from the coordinator."""
        return self.coordinator.data

    @property
    def available(self) -> bool:
        """Return True when the coordinator has valid data."""
        d = self.data
        return d is not None and d.available

    def _base_attrs(self) -> dict:
        """Common attributes for all forecast sensors."""
        d = self.data
        if not d or d.p_now is None:
            return {}
        attrs: dict = {
            "pressure_hpa": d.p_now,
            "pressure_delta_3h": d.delta_3h,
            "trend": d.trend_label,
        }
        if d.altitude is not None:
            attrs["altitude_m"] = d.altitude
        if d.humidity is not None:
            attrs["humidity_%"] = d.humidity
        if d.wind_degrees is not None:
            attrs["wind_direction"] = d.wind_direction
            attrs["wind_degrees"] = d.wind_degrees
        if d.wind_speed is not None:
            attrs["wind_speed"] = d.wind_speed
        if d.is_night:
            attrs["is_night"] = d.is_night
        return attrs


class ZambrettiSensor(WeatherSensorBase):
    """Current Zambretti forecast sensor based on the 3-hour pressure trend."""

    _attr_translation_key = "zambretti_forecast"

    def __init__(self, coordinator: ZambrettiSagerCoordinator) -> None:
        """Initialize the Zambretti forecast sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_zambretti"

    @property
    def native_value(self) -> str | None:
        """Return the current Zambretti forecast translation key."""
        d = self.data
        if not d or not d.available or d.p_now is None:
            return None
        return d.zambretti_state

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes including the source pressure sensor id."""
        attrs = self._base_attrs()
        attrs["pressure_sensor"] = self.coordinator.pressure_id
        return attrs


class SagerSensor(WeatherSensorBase):
    """Sager forecast sensor based on pressure, trend, and wind direction."""

    _attr_translation_key = "sager_forecast"

    def __init__(self, coordinator: ZambrettiSagerCoordinator) -> None:
        """Initialize the Sager forecast sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_sager"

    @property
    def native_value(self) -> str | None:
        """Return the current Sager forecast translation key."""
        d = self.data
        if not d or not d.available or d.p_now is None:
            return None
        return d.sager_state

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes for the Sager forecast."""
        return self._base_attrs()


class ZambrettiForecast6h(WeatherSensorBase):
    """Zambretti forecast sensor for 6 hours ahead (3-hour trend extrapolated ×2)."""

    _attr_translation_key = "zambretti_forecast_6h"
    _attr_icon = "mdi:weather-partly-cloudy"

    def __init__(self, coordinator: ZambrettiSagerCoordinator) -> None:
        """Initialize the 6-hour Zambretti forecast sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_zambretti_6h"

    @property
    def native_value(self) -> str | None:
        """Return the 6-hour Zambretti forecast translation key."""
        d = self.data
        if not d or not d.available or d.p_now is None:
            return None
        return d.zambretti_6h

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes including predicted pressure for 6 hours ahead."""
        attrs = self._base_attrs()
        d = self.data
        if d and d.predicted_p_6h is not None:
            attrs["predicted_pressure_hpa"] = d.predicted_p_6h
        return attrs


class ZambrettiForecast12h(WeatherSensorBase):
    """Zambretti forecast sensor for 12 hours ahead (6-hour trend extrapolated ×2)."""

    _attr_translation_key = "zambretti_forecast_12h"
    _attr_icon = "mdi:weather-cloudy"

    def __init__(self, coordinator: ZambrettiSagerCoordinator) -> None:
        """Initialize the 12-hour Zambretti forecast sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_zambretti_12h"

    @property
    def native_value(self) -> str | None:
        """Return the 12-hour Zambretti forecast translation key."""
        d = self.data
        if not d or not d.available or d.p_now is None:
            return None
        return d.zambretti_12h

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes including predicted pressure for 12 hours ahead."""
        attrs = self._base_attrs()
        d = self.data
        if d and d.predicted_p_12h is not None:
            attrs["predicted_pressure_hpa"] = d.predicted_p_12h
        return attrs


class ZambrettiForecast24h(WeatherSensorBase):
    """Zambretti forecast sensor for 24 hours ahead (12-hour trend extrapolated ×2)."""

    _attr_translation_key = "zambretti_forecast_24h"
    _attr_icon = "mdi:weather-sunset"

    def __init__(self, coordinator: ZambrettiSagerCoordinator) -> None:
        """Initialize the 24-hour Zambretti forecast sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_zambretti_24h"

    @property
    def native_value(self) -> str | None:
        """Return the 24-hour Zambretti forecast translation key."""
        d = self.data
        if not d or not d.available or d.p_now is None:
            return None
        return d.zambretti_24h

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes including predicted pressure for 24 hours ahead."""
        attrs = self._base_attrs()
        d = self.data
        if d and d.predicted_p_24h is not None:
            attrs["predicted_pressure_hpa"] = d.predicted_p_24h
        return attrs


class PrecipitationProbability(WeatherSensorBase):
    """Sensor for precipitation probability based on pressure, trend, and humidity."""

    _attr_translation_key = "precipitation_probability"
    _attr_icon = "mdi:water-percent"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ZambrettiSagerCoordinator) -> None:
        """Initialize the precipitation probability sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_precipitation_probability"

    @property
    def native_value(self) -> int | None:
        """Return precipitation probability as an integer percentage (0–100)."""
        d = self.data
        if not d or not d.available or d.p_now is None:
            return None
        return d.precip_probability

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes for the precipitation probability sensor."""
        return self._base_attrs()


class LastUpdateSensor(WeatherSensorBase):
    """Sensor showing the timestamp of the last successful update."""

    _attr_translation_key = "last_update"
    _attr_icon = "mdi:clock-time-four"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_force_update = True

    def __init__(self, coordinator: ZambrettiSagerCoordinator) -> None:
        """Initialize the last update sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_last_update"

    @property
    def available(self) -> bool:
        """Return True when a last-update timestamp exists."""
        d = self.data
        return d is not None and d.last_updated is not None

    @property
    def native_value(self) -> datetime | None:
        """Return the UTC timestamp of the last successful coordinator update."""
        d = self.data
        if d is None:
            return None
        return d.last_updated
