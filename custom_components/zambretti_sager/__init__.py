"""Zambretti & Sager Weather Forecaster integration for Home Assistant."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.start import async_at_start

from .const import DOMAIN, VERSION
from .coordinator import ZambrettiConfigEntry, async_create_coordinator
from .frontend import JSModuleRegistration

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.WEATHER]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


# ── WebSocket: version endpoint ───────────────────────────────────────────

@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/version"})
@websocket_api.async_response
async def _ws_get_version(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict,
) -> None:
    """Return the integration version to the frontend via WebSocket."""
    connection.send_result(msg["id"], {"version": VERSION})


# ── async_setup ───────────────────────────────────────────────────────────

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Zambretti & Sager domain.

    Called once when Home Assistant loads the integration.
    Registers the WebSocket version command and the Lovelace JavaScript card.
    Must be in async_setup (not async_setup_entry) so the card is available
    before any config entry is created.
    """
    websocket_api.async_register_command(hass, _ws_get_version)

    async def _setup_frontend(_event=None) -> None:
        """Register the custom Lovelace card resource."""
        try:
            registrar = JSModuleRegistration(hass)
            await registrar.async_register()
        except Exception as err:  # noqa: BLE001
            _LOGGER.error(
                "Failed to register Zambretti card resource: %s. "
                "Add manually: Settings → Dashboards → Resources → "
                "%s/zambretti-weather-card.js (JavaScript module)",
                err,
                "/zambretti_sager_card",
            )

    async_at_start(hass, _setup_frontend)
    return True


# ── async_setup_entry ─────────────────────────────────────────────────────

async def async_setup_entry(hass: HomeAssistant, entry: ZambrettiConfigEntry) -> bool:
    """Set up Zambretti & Sager from a config entry (via UI)."""
    _LOGGER.info("Initializing Zambretti & Sager for: %s", entry.title)

    coordinator = await async_create_coordinator(hass, entry)
    entry.runtime_data = coordinator

    # Reload entry when options are updated
    entry.async_on_unload(entry.add_update_listener(_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ZambrettiConfigEntry) -> bool:
    """Unload a config entry (called when entry is removed)."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

