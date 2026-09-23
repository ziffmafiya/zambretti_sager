"""Unit tests for elevation resolution service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.zambretti_sager.elevation import (
    async_resolve_elevation,
)


@pytest.mark.asyncio
async def test_resolve_elevation_configured():
    """Test Local-First: explicitly configured elevation is returned immediately."""
    mock_hass = AsyncMock()
    mock_hass.config.elevation = 150.0

    # Explicit configured elevation overrides
    res = await async_resolve_elevation(
        mock_hass, latitude=55.0, longitude=37.0, configured_elevation=210.0
    )
    assert res == 210.0


@pytest.mark.asyncio
async def test_resolve_elevation_ha_config():
    """Test Local-First: uses hass.config.elevation without making external HTTP requests."""
    mock_hass = AsyncMock()
    mock_hass.config.elevation = 150.0

    with patch(
        "custom_components.zambretti_sager.elevation.get_elevation_from_api",
        new_callable=AsyncMock,
    ) as mock_api:
        res = await async_resolve_elevation(
            mock_hass, latitude=55.0, longitude=37.0, configured_elevation=None
        )
        assert res == 150.0
        mock_api.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_elevation_fallback_to_api():
    """Test fallback to external API when no local elevation is configured."""
    mock_hass = AsyncMock()
    mock_hass.config.elevation = None

    with patch(
        "custom_components.zambretti_sager.elevation.get_elevation_from_api",
        new_callable=AsyncMock,
    ) as mock_api:
        mock_api.return_value = 185.0
        res = await async_resolve_elevation(mock_hass, latitude=55.75, longitude=37.61)

        assert res == 185.0
        mock_api.assert_awaited_once_with(mock_hass, 55.75, 37.61)


@pytest.mark.asyncio
async def test_resolve_elevation_no_coords_no_config():
    """Test returns None gracefully when no coordinates and no local config exist."""
    mock_hass = AsyncMock()
    mock_hass.config.elevation = None

    res = await async_resolve_elevation(mock_hass, latitude=None, longitude=None)
    assert res is None


class MockAsyncContextManager:
    """Helper to mock aiohttp session.get() async context manager."""

    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc, tb):
        return None


@pytest.mark.asyncio
async def test_get_elevation_from_api_open_elevation_success():
    """Test get_elevation_from_api returns elevation from Open-Elevation."""
    from custom_components.zambretti_sager.elevation import (
        _ELEVATION_CACHE,
        get_elevation_from_api,
    )

    _ELEVATION_CACHE.clear()
    mock_hass = AsyncMock()
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"results": [{"elevation": 142.5}]})

    mock_session = MagicMock()
    mock_session.get.return_value = MockAsyncContextManager(mock_resp)

    with patch(
        "custom_components.zambretti_sager.elevation.async_get_clientsession",
        return_value=mock_session,
    ):
        val = await get_elevation_from_api(mock_hass, 50.1234, 14.5678)
        assert val == 142.5

        # Check cache
        val_cached = await get_elevation_from_api(mock_hass, 50.1234, 14.5678)
        assert val_cached == 142.5
        # Only 1 HTTP call made due to cache
        assert mock_session.get.call_count == 1


@pytest.mark.asyncio
async def test_get_elevation_from_api_fallback_to_open_meteo():
    """Test fallback to Open-Meteo when Open-Elevation returns non-200 or fails."""
    from custom_components.zambretti_sager.elevation import (
        _ELEVATION_CACHE,
        get_elevation_from_api,
    )

    _ELEVATION_CACHE.clear()
    mock_hass = AsyncMock()

    mock_resp_oe = AsyncMock()
    mock_resp_oe.status = 500

    mock_resp_om = AsyncMock()
    mock_resp_om.status = 200
    mock_resp_om.json = AsyncMock(return_value={"elevation": [178.0]})

    mock_session = MagicMock()
    mock_session.get.side_effect = [
        MockAsyncContextManager(mock_resp_oe),
        MockAsyncContextManager(mock_resp_om),
    ]

    with patch(
        "custom_components.zambretti_sager.elevation.async_get_clientsession",
        return_value=mock_session,
    ):
        val = await get_elevation_from_api(mock_hass, 52.0, 13.0)
        assert val == 178.0


@pytest.mark.asyncio
async def test_get_elevation_from_api_all_fail():
    """Test returns None when both elevation APIs fail or raise exceptions."""
    from custom_components.zambretti_sager.elevation import (
        _ELEVATION_CACHE,
        get_elevation_from_api,
    )

    _ELEVATION_CACHE.clear()
    mock_hass = AsyncMock()
    mock_session = MagicMock()
    mock_session.get.side_effect = Exception("Connection error")

    with patch(
        "custom_components.zambretti_sager.elevation.async_get_clientsession",
        return_value=mock_session,
    ):
        val = await get_elevation_from_api(mock_hass, 52.0, 13.0)
        assert val is None
