"""Sensor platform for the Zambretti & Sager integration."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    VERSION,
    ZAMBRETTI_MAPPING,
    calculate_sager_forecast,
    classify_pressure_trend,
    wind_degrees_to_compass,
)
from .coordinator import ForecastData, ZambrettiSagerCoordinator


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Zambretti & Sager sensors."""
    coordinator: ZambrettiSagerCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        ZambrettiSensor(coordinator),
        SagerSensor(coordinator),
        ZambrettiForecast6h(coordinator),
        ZambrettiForecast12h(coordinator),
        ZambrettiForecast24h(coordinator),
        PrecipitationProbability(coordinator),
        LastUpdateSensor(coordinator),
    ])


def _trend_label(delta: float) -> str:
    """Return human-readable trend label for attributes."""
    trend = classify_pressure_trend(delta)
    return {
        "rising_rapidly": "↑↑ Rising Fast",
        "rising_slowly":  "↑ Rising",
        "steady":         "→ Steady",
        "falling_slowly": "↓ Falling",
        "falling_rapidly":"↓↓ Falling Fast",
    }.get(trend, "→ Steady")


class WeatherSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for all forecast sensors."""

    # Force HA to write a recorder entry every coordinator update cycle
    # (every 5 min) even when state hasn't changed. This gives the Lovelace
    # history chart and trend timeline dense data to work with.
    _attr_force_update = True

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
        self._attr_has_entity_name = True

    @property
    def data(self) -> ForecastData | None:
        """Return the latest forecast data snapshot from the coordinator."""
        return self.coordinator.data

    @property
    def available(self) -> bool:
        """Return True when the coordinator has valid data."""
        d = self.data
        return d is not None and d.available

    @staticmethod
    def _zambretti_index(p_now: float, delta: float) -> int:
        """Calculate Zambretti index (1–32) from pressure and 3h trend.

        The original Zambretti algorithm uses different formulas for
        falling, steady, and rising pressure trends.
        """
        if delta <= -1.6:        # Falling
            z = round(127 - 0.12 * p_now)
        elif delta >= 1.6:       # Rising
            z = round(185 - 0.16 * p_now)
        else:                    # Steady
            z = round(144 - 0.13 * p_now)
        return max(1, min(z, 32))

    def _base_attrs(self, delta: float) -> dict:
        """Common attributes for all forecast sensors."""
        d = self.data
        attrs: dict = {}
        if d and d.p_now is not None:
            attrs["pressure_hpa"] = round(d.p_now, 1)
            attrs["pressure_delta_3h"] = round(d.p_now - d.p_3h, 2) if d.p_3h else None
            attrs["trend"] = _trend_label(delta)
        if d and d.altitude is not None:
            attrs["altitude_m"] = round(d.altitude, 1)
        if d and d.humidity is not None:
            attrs["humidity_%"] = round(d.humidity, 1)
        if d and d.wind_degrees is not None:
            attrs["wind_direction"] = wind_degrees_to_compass(d.wind_degrees)
            attrs["wind_degrees"] = round(d.wind_degrees, 1)
        if d and d.wind_speed is not None:
            attrs["wind_speed"] = round(d.wind_speed, 1)
        if d and d.is_night:
            attrs["is_night"] = d.is_night
        return attrs


class ZambrettiSensor(WeatherSensorBase):
    """Current Zambretti forecast sensor based on the 3-hour pressure trend."""

    def __init__(self, coordinator: ZambrettiSagerCoordinator) -> None:
        """Initialize the Zambretti forecast sensor."""
        super().__init__(coordinator)
        self._attr_name = "Zambretti Forecast"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_zambretti"

    @property
    def native_value(self) -> str | None:
        """Return the current Zambretti forecast translation key."""
        d = self.data
        if not d or not d.available or d.p_now is None:
            return None
        # Use p_3h if available, otherwise assume steady trend (delta=0)
        p_3h = d.p_3h if d.p_3h is not None else d.p_now
        delta = d.p_now - p_3h
        return ZAMBRETTI_MAPPING.get(self._zambretti_index(d.p_now, delta), "stable")

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes including the source pressure sensor id."""
        d = self.data
        if not d or d.p_now is None:
            return {}
        p_3h = d.p_3h if d.p_3h is not None else d.p_now
        delta = d.p_now - p_3h
        attrs = self._base_attrs(delta)
        # Expose the raw pressure sensor entity_id so the Lovelace card
        # can fetch its history directly (much denser than Zambretti state changes)
        attrs["pressure_sensor"] = self.coordinator.pressure_id
        return attrs


class SagerSensor(WeatherSensorBase):
    """Sager forecast sensor based on pressure, trend, and wind direction."""

    def __init__(self, coordinator: ZambrettiSagerCoordinator) -> None:
        """Initialize the Sager forecast sensor."""
        super().__init__(coordinator)
        self._attr_name = "Sager Forecast"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_sager"

    @property
    def native_value(self) -> str | None:
        """Return the current Sager forecast translation key."""
        d = self.data
        if not d or not d.available or d.p_now is None:
            return None
        p_3h = d.p_3h if d.p_3h is not None else d.p_now
        delta = d.p_now - p_3h
        return calculate_sager_forecast(d.p_now, delta, d.wind_degrees)

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes for the Sager forecast."""
        d = self.data
        if not d or d.p_now is None:
            return {}
        p_3h = d.p_3h if d.p_3h is not None else d.p_now
        delta = d.p_now - p_3h
        return self._base_attrs(delta)


class ZambrettiForecast6h(WeatherSensorBase):
    """Zambretti forecast sensor for 6 hours ahead (3-hour trend extrapolated ×2)."""

    def __init__(self, coordinator: ZambrettiSagerCoordinator) -> None:
        """Initialize the 6-hour Zambretti forecast sensor."""
        super().__init__(coordinator)
        self._attr_name = "Zambretti Forecast 6h"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_zambretti_6h"
        self._attr_icon = "mdi:weather-partly-cloudy"

    @property
    def native_value(self) -> str | None:
        """Return the 6-hour Zambretti forecast translation key."""
        d = self.data
        if not d or not d.available or d.p_now is None:
            return None
        p_3h = d.p_3h if d.p_3h is not None else d.p_now
        delta_6h = (d.p_now - p_3h) * 2
        predicted = d.p_now + delta_6h
        return ZAMBRETTI_MAPPING.get(self._zambretti_index(predicted, delta_6h), "stable")

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes including predicted pressure for 6 hours ahead."""
        d = self.data
        if not d or d.p_now is None:
            return {}
        p_3h = d.p_3h if d.p_3h is not None else d.p_now
        delta_6h = (d.p_now - p_3h) * 2
        attrs = self._base_attrs(delta_6h)
        attrs["predicted_pressure_hpa"] = round(d.p_now + delta_6h, 1)
        return attrs


class ZambrettiForecast12h(WeatherSensorBase):
    """Zambretti forecast sensor for 12 hours ahead (6-hour trend extrapolated ×2)."""

    def __init__(self, coordinator: ZambrettiSagerCoordinator) -> None:
        """Initialize the 12-hour Zambretti forecast sensor."""
        super().__init__(coordinator)
        self._attr_name = "Zambretti Forecast 12h"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_zambretti_12h"
        self._attr_icon = "mdi:weather-cloudy"

    @property
    def native_value(self) -> str | None:
        """Return the 12-hour Zambretti forecast translation key."""
        d = self.data
        if not d or not d.available or d.p_now is None:
            return None
        # Use 6h history if available, else fall back to 3h, else steady
        p_ref = d.p_6h if d.p_6h is not None else (d.p_3h if d.p_3h is not None else d.p_now)
        hours = 6 if d.p_6h is not None else (3 if d.p_3h is not None else 1)
        delta_12h = (d.p_now - p_ref) / hours * 12
        predicted = d.p_now + delta_12h
        return ZAMBRETTI_MAPPING.get(self._zambretti_index(predicted, delta_12h), "stable")

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes including predicted pressure for 12 hours ahead."""
        d = self.data
        if not d or d.p_now is None:
            return {}
        p_ref = d.p_6h if d.p_6h is not None else (d.p_3h if d.p_3h is not None else d.p_now)
        hours = 6 if d.p_6h is not None else (3 if d.p_3h is not None else 1)
        delta_12h = (d.p_now - p_ref) / hours * 12
        attrs = self._base_attrs(delta_12h)
        attrs["predicted_pressure_hpa"] = round(d.p_now + delta_12h, 1)
        return attrs


class ZambrettiForecast24h(WeatherSensorBase):
    """Zambretti forecast sensor for 24 hours ahead (12-hour trend extrapolated ×2)."""

    def __init__(self, coordinator: ZambrettiSagerCoordinator) -> None:
        """Initialize the 24-hour Zambretti forecast sensor."""
        super().__init__(coordinator)
        self._attr_name = "Zambretti Forecast 24h"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_zambretti_24h"
        self._attr_icon = "mdi:weather-sunset"

    @property
    def native_value(self) -> str | None:
        """Return the 24-hour Zambretti forecast translation key."""
        d = self.data
        if not d or not d.available or d.p_now is None:
            return None
        # Use 12h history if available, else best available, else steady
        p_ref = d.p_12h if d.p_12h is not None else (
                d.p_6h  if d.p_6h  is not None else (
                d.p_3h  if d.p_3h  is not None else d.p_now))
        hours = (12 if d.p_12h is not None else
                  6 if d.p_6h  is not None else
                  3 if d.p_3h  is not None else 1)
        delta_24h = (d.p_now - p_ref) / hours * 24
        predicted = d.p_now + delta_24h
        return ZAMBRETTI_MAPPING.get(self._zambretti_index(predicted, delta_24h), "stable")

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes including predicted pressure for 24 hours ahead."""
        d = self.data
        if not d or d.p_now is None:
            return {}
        p_ref = d.p_12h if d.p_12h is not None else (
                d.p_6h  if d.p_6h  is not None else (
                d.p_3h  if d.p_3h  is not None else d.p_now))
        hours = (12 if d.p_12h is not None else
                  6 if d.p_6h  is not None else
                  3 if d.p_3h  is not None else 1)
        delta_24h = (d.p_now - p_ref) / hours * 24
        attrs = self._base_attrs(delta_24h)
        attrs["predicted_pressure_hpa"] = round(d.p_now + delta_24h, 1)
        return attrs


class PrecipitationProbability(WeatherSensorBase):
    """Sensor for precipitation probability based on pressure, trend, and humidity."""

    def __init__(self, coordinator: ZambrettiSagerCoordinator) -> None:
        """Initialize the precipitation probability sensor."""
        super().__init__(coordinator)
        self._attr_name = "Precipitation Probability"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_precipitation_probability"
        self._attr_icon = "mdi:water-percent"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | None:
        """Return precipitation probability as an integer percentage (0–100)."""
        d = self.data
        if not d or not d.available or d.p_now is None:
            return None

        p_3h = d.p_3h if d.p_3h is not None else d.p_now
        delta = d.p_now - p_3h
        p_now = d.p_now

        # Base probability from current pressure
        if p_now < 1000:       base_prob = 90
        elif p_now < 1005:     base_prob = 70
        elif p_now < 1010:     base_prob = 50
        elif p_now < 1015:     base_prob = 30
        elif p_now < 1020:     base_prob = 15
        else:                  base_prob = 5

        # Trend modifier
        if delta < -3.0:       trend_modifier = 30
        elif delta < -1.6:     trend_modifier = 15
        elif delta > 3.0:      trend_modifier = -30
        elif delta > 1.6:      trend_modifier = -15
        else:                  trend_modifier = 0

        # Humidity modifier: high humidity increases precipitation chance
        humidity_modifier = 0
        if d.humidity is not None:
            if d.humidity >= 90:    humidity_modifier = 15
            elif d.humidity >= 80:  humidity_modifier = 10
            elif d.humidity >= 70:  humidity_modifier = 5
            elif d.humidity <= 30:  humidity_modifier = -15
            elif d.humidity <= 40:  humidity_modifier = -10

        return round(max(0, min(100, base_prob + trend_modifier + humidity_modifier)))

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes for the precipitation probability sensor."""
        d = self.data
        if not d or d.p_now is None:
            return {}
        p_3h = d.p_3h if d.p_3h is not None else d.p_now
        delta = d.p_now - p_3h
        attrs = self._base_attrs(delta)
        return attrs


class LastUpdateSensor(WeatherSensorBase):
    """Diagnostic sensor showing the timestamp of the last successful update."""

    def __init__(self, coordinator: ZambrettiSagerCoordinator) -> None:
        """Initialize the last update diagnostic sensor."""
        super().__init__(coordinator)
        self._attr_name = "Last Update"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_last_update"
        self._attr_icon = "mdi:clock-time-four"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_entity_category = "diagnostic"

    @property
    def native_value(self) -> datetime | None:
        """Return the UTC timestamp of the last successful coordinator update."""
        d = self.data
        if d is None:
            return None
        return d.last_updated
