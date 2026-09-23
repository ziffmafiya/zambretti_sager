"""Elevation resolution service: Local-First resolution with external API fallback."""

from __future__ import annotations

import logging

try:
    import aiohttp
except ImportError:  # pragma: no cover
    aiohttp = None  # type: ignore[assignment]

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

_ELEVATION_CACHE: dict[tuple[float, float], float] = {}


async def get_elevation_from_api(
    hass: HomeAssistant, latitude: float, longitude: float
) -> float | None:
    """Fetch elevation above sea level via Open-Elevation or Open-Meteo API.

    Caches results in memory to avoid repetitive HTTP requests across reloads.
    """
    cache_key = (round(float(latitude), 4), round(float(longitude), 4))
    if cache_key in _ELEVATION_CACHE:
        return _ELEVATION_CACHE[cache_key]

    session = async_get_clientsession(hass)
    timeout = aiohttp.ClientTimeout(total=10.0, connect=5.0) if aiohttp is not None else 10.0

    # 1. Try Open-Elevation API
    url_open_elevation = (
        f"https://api.open-elevation.com/api/v1/lookup?locations={latitude},{longitude}"
    )
    try:
        async with session.get(url_open_elevation, timeout=timeout) as response:
            if response.status == 200:
                data = await response.json()
                results = data.get("results")
                if results and "elevation" in results[0]:
                    elevation = float(results[0]["elevation"])
                    _ELEVATION_CACHE[cache_key] = elevation
                    return elevation
    except Exception as err:
        _LOGGER.debug("Failed to get elevation from Open-Elevation API: %s", err)

    # 2. Try Open-Meteo API fallback
    url_open_meteo = (
        f"https://api.open-meteo.com/v1/elevation?latitude={latitude}&longitude={longitude}"
    )
    try:
        async with session.get(url_open_meteo, timeout=timeout) as response:
            if response.status == 200:
                data = await response.json()
                elevations = data.get("elevation")
                if elevations and isinstance(elevations, list) and len(elevations) > 0:
                    elevation = float(elevations[0])
                    _ELEVATION_CACHE[cache_key] = elevation
                    return elevation
    except Exception as err:
        _LOGGER.debug("Failed to get elevation from Open-Meteo API: %s", err)

    return None


# Backward compatibility alias
get_elevation = get_elevation_from_api


async def async_resolve_elevation(
    hass: HomeAssistant,
    latitude: float | None = None,
    longitude: float | None = None,
    configured_elevation: float | None = None,
) -> float | None:
    """Resolve station elevation using a Local-First strategy.

    1. Checks explicitly configured elevation or Home Assistant's configured elevation.
    2. Only if local elevation is unavailable and GPS coordinates are provided,
       queries public elevation APIs.
    """
    # 1. Check explicitly passed or HA-configured elevation (Local-First)
    if configured_elevation is not None:
        _LOGGER.debug("Using explicitly configured elevation: %.1f m", configured_elevation)
        return float(configured_elevation)

    ha_elevation = getattr(getattr(hass, "config", None), "elevation", None)
    if ha_elevation is not None:
        try:
            elevation_val = float(ha_elevation)
            _LOGGER.info("Using Home Assistant configured elevation: %.1f m", elevation_val)
            return elevation_val
        except (ValueError, TypeError):
            pass

    # 2. Fallback to external API lookup if coordinates are available
    if latitude is not None and longitude is not None:
        _LOGGER.debug("Looking up elevation for coordinates (%.4f, %.4f)", latitude, longitude)
        elevation = await get_elevation_from_api(hass, latitude, longitude)
        if elevation is not None:
            _LOGGER.info("Retrieved altitude from external API: %.1f m", elevation)
            return elevation

    _LOGGER.warning("Could not determine altitude, sea level correction will use raw pressure")
    return None
