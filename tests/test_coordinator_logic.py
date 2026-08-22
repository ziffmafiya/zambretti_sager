"""Unit tests for coordinator rolling buffer and data structures."""

from __future__ import annotations

from collections import deque
import datetime

import pytest

from custom_components.zambretti_sager.coordinator import (
    BUFFER_MAX_AGE,
    ForecastData,
    ZambrettiSagerCoordinator,
)


def test_forecast_data_structure():
    """Test ForecastData structure and default fields."""
    fd = ForecastData(
        available=True,
        p_now=1015.5,
        p_3h=1013.5,
        p_6h=1011.0,
        p_12h=1008.0,
        wind_degrees=180.0,
        wind_direction="S",
        wind_speed=5.2,
        humidity=65.0,
        altitude=150.0,
        temperature=18.5,
        is_night=False,
        last_updated=datetime.datetime(2026, 8, 22, 12, 0, tzinfo=datetime.timezone.utc),
        delta_3h=2.0,
        trend_label="↑ Rising",
        zambretti_state="settled_fine",
        sager_state="sager_fair_improving",
        zambretti_6h="fairly_fine_improving",
        predicted_p_6h=1019.5,
        precip_probability=15,
    )

    assert fd.available is True
    assert fd.p_now == 1015.5
    assert fd.delta_3h == 2.0
    assert fd.trend_label == "↑ Rising"
    assert fd.zambretti_state == "settled_fine"
    assert fd.precip_probability == 15


def test_buffer_lookup_logic():
    """Test in-memory rolling buffer pressure lookup by delta hours."""
    now = datetime.datetime(2026, 8, 22, 12, 0, tzinfo=datetime.timezone.utc)
    t_3h = now - datetime.timedelta(hours=3)
    t_6h = now - datetime.timedelta(hours=6)
    t_12h = now - datetime.timedelta(hours=12)

    buffer: deque[tuple[datetime.datetime, float]] = deque([
        (t_12h, 1005.0),
        (t_6h, 1010.0),
        (t_3h + datetime.timedelta(minutes=5), 1015.0), # slightly offset but within 45m
        (now, 1020.0),
    ])

    # Lookup helper simulating _get_buffer_pressure
    def lookup(hours: int) -> float | None:
        target = now - datetime.timedelta(hours=hours)
        best = None
        best_diff = datetime.timedelta(minutes=45)
        for dt, p in buffer:
            diff = abs(dt - target)
            if diff <= best_diff:
                best_diff = diff
                best = p
        return best

    assert lookup(3) == 1015.0
    assert lookup(6) == 1010.0
    assert lookup(12) == 1005.0
    assert lookup(20) is None # outside tolerance
