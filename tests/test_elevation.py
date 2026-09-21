"""Unit tests for elevation resolution service."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

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
