"""JavaScript module registration for Zambretti & Sager card."""
# Tested against HA 2026.x where hass.data uses LOVELACE_DATA key
# and LovelaceData has resource_mode (not mode) attribute.
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

from ..const import JSMODULES, URL_BASE

_LOGGER = logging.getLogger(__name__)

# HA 2025+ stores lovelace data under this key
_LOVELACE_DATA_KEY = "lovelace"

# Constant introduced in HA 2025/2026 — import defensively
try:
    from homeassistant.components.lovelace.const import LOVELACE_DATA
    _LOVELACE_DATA_KEY = LOVELACE_DATA
except ImportError:
    _LOVELACE_DATA_KEY = "lovelace"


def _get_lovelace(hass: HomeAssistant) -> Any | None:
    """Получить объект LovelaceData из hass.data — поддерживает старый и новый ключ."""
    data = hass.data.get(_LOVELACE_DATA_KEY)
    if data is None:
        # Fallback: старый ключ "lovelace"
        data = hass.data.get("lovelace")
    return data


def _get_resource_mode(lovelace: Any) -> str:
    """Получить режим ресурсов безопасно.

    В HA 2026: LovelaceData.resource_mode
    В старых HA: lovelace.mode или lovelace.resource_mode
    """
    # Новый атрибут (HA 2026+)
    if hasattr(lovelace, "resource_mode"):
        return lovelace.resource_mode
    # Старый атрибут
    if hasattr(lovelace, "mode"):
        return lovelace.mode
    return "yaml"


class JSModuleRegistration:
    """Registers JavaScript modules in Home Assistant."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.lovelace = _get_lovelace(hass)

    async def async_register(self) -> None:
        """Register static path + Lovelace resource."""
        await self._async_register_path()

        if self.lovelace is None:
            _LOGGER.warning(
                "Lovelace data not found — add resource manually: "
                "Settings → Dashboards → Resources → %s/zambretti-weather-card.js (JavaScript module)",
                URL_BASE,
            )
            return

        mode = _get_resource_mode(self.lovelace)
        _LOGGER.debug("Lovelace resource_mode = %s", mode)

        if mode == "storage":
            await self._async_wait_for_lovelace_resources()
        else:
            _LOGGER.info(
                "Lovelace YAML mode — add to ui-lovelace.yaml:\n"
                "resources:\n  - url: %s/zambretti-weather-card.js\n    type: module",
                URL_BASE,
            )

    async def _async_register_path(self) -> None:
        """Serve the frontend/ folder as a static HTTP endpoint."""
        try:
            await self.hass.http.async_register_static_paths(
                [StaticPathConfig(URL_BASE, Path(__file__).parent, False)]
            )
            _LOGGER.debug("Static path registered: %s", URL_BASE)
        except RuntimeError:
            _LOGGER.debug("Static path already registered: %s", URL_BASE)

    async def _async_wait_for_lovelace_resources(self) -> None:
        """Wait until Lovelace resources collection is loaded (max 10 retries)."""

        self._lovelace_retries = 0

        async def _check(_now: Any) -> None:
            if self.lovelace.resources.loaded:
                await self._async_register_modules()
                return
            self._lovelace_retries += 1
            if self._lovelace_retries >= 10:
                _LOGGER.warning(
                    "Lovelace resources did not load after 10 attempts — "
                    "add resource manually: "
                    "Settings → Dashboards → Resources → %s/zambretti-weather-card.js",
                    URL_BASE,
                )
                return
            _LOGGER.debug(
                "Lovelace resources not loaded yet, retrying in 5s (attempt %d/10)",
                self._lovelace_retries,
            )
            async_call_later(self.hass, 5, _check)

        await _check(0)

    async def _async_register_modules(self) -> None:
        """Add or update JS module entries in Lovelace storage."""
        _LOGGER.debug("Installing Zambretti javascript modules")

        existing = [
            r for r in self.lovelace.resources.async_items()
            if r["url"].startswith(URL_BASE)
        ]

        for module in JSMODULES:
            url = f"{URL_BASE}/{module['filename']}"
            expected_url = f"{url}?v={module['version']}"
            matching = [
                r for r in existing
                if self._get_path(r["url"]) == url
            ]

            if not matching:
                _LOGGER.info("Registering %s v%s", module["name"], module["version"])
                await self.lovelace.resources.async_create_item(
                    {"res_type": "module", "url": expected_url}
                )
            else:
                primary = matching[0]
                if primary["url"] != expected_url:
                    _LOGGER.info("Updating %s to v%s", module["name"], module["version"])
                    await self.lovelace.resources.async_update_item(
                        primary["id"],
                        {"res_type": "module", "url": expected_url},
                    )
                else:
                    _LOGGER.debug("%s already up to date (v%s)", module["name"], module["version"])

                # Remove any duplicate Lovelace resource entries
                for dup in matching[1:]:
                    _LOGGER.info("Removing duplicate Lovelace resource: %s", dup["url"])
                    await self.lovelace.resources.async_delete_item(dup["id"])

    def _get_path(self, url: str) -> str:
        return url.split("?")[0]

    def _get_version(self, url: str) -> str:
        parts = url.split("?")
        if len(parts) > 1 and parts[1].startswith("v="):
            return parts[1][2:]
        return "0"

    async def async_unregister(self) -> None:
        """Remove Lovelace resource entries on uninstall."""
        if self.lovelace is None or _get_resource_mode(self.lovelace) != "storage":
            return
        for module in JSMODULES:
            url = f"{URL_BASE}/{module['filename']}"
            to_remove = [
                r for r in self.lovelace.resources.async_items()
                if r["url"].startswith(url)
            ]
            for resource in to_remove:
                await self.lovelace.resources.async_delete_item(resource["id"])
                _LOGGER.info("Lovelace resource removed: %s", resource["url"])
