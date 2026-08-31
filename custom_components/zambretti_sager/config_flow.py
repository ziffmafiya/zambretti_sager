"""Config flow for the Zambretti & Sager integration."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
import voluptuous as vol

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
)

CONF_LOCATION = "location"
OPTIONAL_ENTITY_KEYS = (
    CONF_WIND_SENSOR,
    CONF_WIND_SPEED_SENSOR,
    CONF_TEMPERATURE_SENSOR,
    CONF_HUMIDITY_SENSOR,
)

PRESSURE_SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        domain="sensor",
        device_class=["atmospheric_pressure", "pressure"],
    )
)

WIND_SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        domain="sensor",
    )
)

WIND_SPEED_SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        domain="sensor",
    )
)

TEMPERATURE_SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        domain="sensor",
        device_class="temperature",
    )
)

HUMIDITY_SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        domain="sensor",
        device_class="humidity",
    )
)


def _normalize_optional_entities(data: dict) -> dict:
    """Remove empty optional sensor entries from config data."""
    normalized = dict(data)
    for key in OPTIONAL_ENTITY_KEYS:
        val = normalized.get(key)
        if val is None or (isinstance(val, str) and not val.strip()):
            normalized.pop(key, None)
    return normalized


def _apply_location(data: dict) -> dict:
    """Extract latitude/longitude from the location selector."""
    normalized = dict(data)
    if CONF_LOCATION in normalized:
        location = normalized.pop(CONF_LOCATION)
        normalized[CONF_LATITUDE] = location.get("latitude")
        normalized[CONF_LONGITUDE] = location.get("longitude")
    return normalized


class ZambrettiSagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for setting up a new Zambretti & Sager entry."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step shown to the user."""
        if user_input is not None:
            user_input = _normalize_optional_entities(_apply_location(user_input))

            # Use the pressure sensor entity_id as unique_id to prevent
            # duplicate entries for the same sensor
            await self.async_set_unique_id(f"{DOMAIN}_{user_input[CONF_PRESSURE_SENSOR]}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title="Weather Forecaster", data=user_input)

        default_location = {
            "latitude": self.hass.config.latitude,
            "longitude": self.hass.config.longitude,
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PRESSURE_SENSOR): PRESSURE_SENSOR_SELECTOR,
                    vol.Optional(CONF_WIND_SENSOR): WIND_SENSOR_SELECTOR,
                    vol.Optional(CONF_WIND_SPEED_SENSOR): WIND_SPEED_SENSOR_SELECTOR,
                    vol.Optional(CONF_TEMPERATURE_SENSOR): TEMPERATURE_SENSOR_SELECTOR,
                    vol.Optional(CONF_HUMIDITY_SENSOR): HUMIDITY_SENSOR_SELECTOR,
                    vol.Optional(CONF_USE_SEA_LEVEL, default=False): selector.BooleanSelector(),
                    vol.Optional(
                        CONF_LOCATION, default=default_location
                    ): selector.LocationSelector(
                        selector.LocationSelectorConfig(radius=False, icon="mdi:map-marker")
                    ),
                }
            ),
        )

    async def async_step_reconfigure(self, user_input=None):
        """Handle reconfiguring an existing Zambretti & Sager entry."""
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            user_input = _normalize_optional_entities(_apply_location(user_input))
            new_unique_id = f"{DOMAIN}_{user_input[CONF_PRESSURE_SENSOR]}"
            await self.async_set_unique_id(new_unique_id)
            self._abort_if_unique_id_mismatch(reason="already_configured")

            return self.async_update_reload_and_abort(
                entry,
                data={**entry.data, **user_input},
                reason="reconfigure_successful",
            )

        current_pressure = entry.options.get(CONF_PRESSURE_SENSOR) or entry.data.get(
            CONF_PRESSURE_SENSOR
        )
        current_wind = entry.options.get(CONF_WIND_SENSOR) or entry.data.get(CONF_WIND_SENSOR)
        current_wind_speed = entry.options.get(CONF_WIND_SPEED_SENSOR) or entry.data.get(
            CONF_WIND_SPEED_SENSOR
        )
        current_temp = entry.options.get(CONF_TEMPERATURE_SENSOR) or entry.data.get(
            CONF_TEMPERATURE_SENSOR
        )
        current_humidity = entry.options.get(CONF_HUMIDITY_SENSOR) or entry.data.get(
            CONF_HUMIDITY_SENSOR
        )
        current_use_sea_level = (
            entry.options.get(CONF_USE_SEA_LEVEL)
            if CONF_USE_SEA_LEVEL in entry.options
            else entry.data.get(CONF_USE_SEA_LEVEL, False)
        )
        current_lat = entry.options.get(CONF_LATITUDE) or entry.data.get(CONF_LATITUDE)
        current_lon = entry.options.get(CONF_LONGITUDE) or entry.data.get(CONF_LONGITUDE)

        default_location = {
            "latitude": current_lat if current_lat is not None else self.hass.config.latitude,
            "longitude": current_lon if current_lon is not None else self.hass.config.longitude,
        }

        schema_dict = {
            vol.Required(CONF_PRESSURE_SENSOR, default=current_pressure): PRESSURE_SENSOR_SELECTOR,
        }
        if current_wind:
            schema_dict[vol.Optional(CONF_WIND_SENSOR, default=current_wind)] = WIND_SENSOR_SELECTOR
        else:
            schema_dict[vol.Optional(CONF_WIND_SENSOR)] = WIND_SENSOR_SELECTOR

        if current_wind_speed:
            schema_dict[vol.Optional(CONF_WIND_SPEED_SENSOR, default=current_wind_speed)] = (
                WIND_SPEED_SENSOR_SELECTOR
            )
        else:
            schema_dict[vol.Optional(CONF_WIND_SPEED_SENSOR)] = WIND_SPEED_SENSOR_SELECTOR

        if current_temp:
            schema_dict[vol.Optional(CONF_TEMPERATURE_SENSOR, default=current_temp)] = (
                TEMPERATURE_SENSOR_SELECTOR
            )
        else:
            schema_dict[vol.Optional(CONF_TEMPERATURE_SENSOR)] = TEMPERATURE_SENSOR_SELECTOR

        if current_humidity:
            schema_dict[vol.Optional(CONF_HUMIDITY_SENSOR, default=current_humidity)] = (
                HUMIDITY_SENSOR_SELECTOR
            )
        else:
            schema_dict[vol.Optional(CONF_HUMIDITY_SENSOR)] = HUMIDITY_SENSOR_SELECTOR

        schema_dict[vol.Optional(CONF_USE_SEA_LEVEL, default=current_use_sea_level)] = (
            selector.BooleanSelector()
        )
        schema_dict[vol.Optional(CONF_LOCATION, default=default_location)] = (
            selector.LocationSelector(
                selector.LocationSelectorConfig(radius=False, icon="mdi:map-marker")
            )
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(schema_dict),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow handler for this entry."""
        return ZambrettiSagerOptionsFlowHandler(config_entry)


class ZambrettiSagerOptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow for updating an existing Zambretti & Sager entry."""

    def __init__(self, config_entry) -> None:
        """Store the config entry being reconfigured."""
        super().__init__()
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle the options form, pre-populated with current settings."""
        if user_input is not None:
            user_input = _normalize_optional_entities(_apply_location(user_input))
            return self.async_create_entry(title="", data=user_input)

        entry = self._config_entry
        # Read current values from options first, fall back to data
        current_pressure = entry.options.get(CONF_PRESSURE_SENSOR) or entry.data.get(
            CONF_PRESSURE_SENSOR
        )
        current_wind = entry.options.get(CONF_WIND_SENSOR) or entry.data.get(CONF_WIND_SENSOR)
        current_wind_speed = entry.options.get(CONF_WIND_SPEED_SENSOR) or entry.data.get(
            CONF_WIND_SPEED_SENSOR
        )
        current_temp = entry.options.get(CONF_TEMPERATURE_SENSOR) or entry.data.get(
            CONF_TEMPERATURE_SENSOR
        )
        current_humidity = entry.options.get(CONF_HUMIDITY_SENSOR) or entry.data.get(
            CONF_HUMIDITY_SENSOR
        )
        current_use_sea_level = (
            entry.options.get(CONF_USE_SEA_LEVEL)
            if CONF_USE_SEA_LEVEL in entry.options
            else entry.data.get(CONF_USE_SEA_LEVEL, False)
        )
        current_lat = entry.options.get(CONF_LATITUDE) or entry.data.get(CONF_LATITUDE)
        current_lon = entry.options.get(CONF_LONGITUDE) or entry.data.get(CONF_LONGITUDE)

        if current_lat is not None and current_lon is not None:
            default_location = {
                "latitude": current_lat,
                "longitude": current_lon,
            }
        else:
            default_location = {
                "latitude": self.hass.config.latitude,
                "longitude": self.hass.config.longitude,
            }

        # Build schema — optional fields with None default are omitted
        # to avoid voluptuous validation errors on invalid entity_id
        schema_dict = {
            vol.Required(CONF_PRESSURE_SENSOR, default=current_pressure): PRESSURE_SENSOR_SELECTOR,
        }

        if current_wind:
            schema_dict[vol.Optional(CONF_WIND_SENSOR, default=current_wind)] = WIND_SENSOR_SELECTOR
        else:
            schema_dict[vol.Optional(CONF_WIND_SENSOR)] = WIND_SENSOR_SELECTOR

        if current_wind_speed:
            schema_dict[vol.Optional(CONF_WIND_SPEED_SENSOR, default=current_wind_speed)] = (
                WIND_SPEED_SENSOR_SELECTOR
            )
        else:
            schema_dict[vol.Optional(CONF_WIND_SPEED_SENSOR)] = WIND_SPEED_SENSOR_SELECTOR

        if current_temp:
            schema_dict[vol.Optional(CONF_TEMPERATURE_SENSOR, default=current_temp)] = (
                TEMPERATURE_SENSOR_SELECTOR
            )
        else:
            schema_dict[vol.Optional(CONF_TEMPERATURE_SENSOR)] = TEMPERATURE_SENSOR_SELECTOR

        if current_humidity:
            schema_dict[vol.Optional(CONF_HUMIDITY_SENSOR, default=current_humidity)] = (
                HUMIDITY_SENSOR_SELECTOR
            )
        else:
            schema_dict[vol.Optional(CONF_HUMIDITY_SENSOR)] = HUMIDITY_SENSOR_SELECTOR

        schema_dict[vol.Optional(CONF_USE_SEA_LEVEL, default=current_use_sea_level)] = (
            selector.BooleanSelector()
        )
        schema_dict[vol.Optional(CONF_LOCATION, default=default_location)] = (
            selector.LocationSelector(
                selector.LocationSelectorConfig(radius=False, icon="mdi:map-marker")
            )
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
        )
