"""Unit tests for PressureHistoryBuffer and recorder batch queries."""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.zambretti_sager.history import (
    BUFFER_MAX_AGE,
    PressureHistoryBuffer,
    async_get_history_pressure_from_recorder,
    async_get_history_pressures_batch_from_recorder,
    async_warm_history_buffer,
)


def test_pressure_history_buffer_append_and_lookup():
    """Test appending points and looking up by target time."""
    buffer = PressureHistoryBuffer()
    now = datetime.datetime(2026, 9, 21, 14, 0, tzinfo=datetime.UTC)

    buffer.append(now - datetime.timedelta(hours=3), 1012.0)
    buffer.append(now - datetime.timedelta(hours=1), 1014.0)
    buffer.append(now, 1015.0)

    assert len(buffer) == 3

    # Exact lookup
    p_3h = buffer.get_pressure_at(now - datetime.timedelta(hours=3))
    assert p_3h == 1012.0

    # Within default 45m tolerance (3h 20m ago matches 3h ago point)
    p_near = buffer.get_pressure_at(now - datetime.timedelta(hours=3, minutes=20))
    assert p_near == 1012.0

    # Outside tolerance
    p_far = buffer.get_pressure_at(now - datetime.timedelta(hours=5))
    assert p_far is None


def test_pressure_history_buffer_out_of_order_appends():
    """Test that out-of-order appends maintain chronological sorting for binary search."""
    buffer = PressureHistoryBuffer()
    t1 = datetime.datetime(2026, 9, 21, 10, 0, tzinfo=datetime.UTC)
    t2 = datetime.datetime(2026, 9, 21, 11, 0, tzinfo=datetime.UTC)
    t3 = datetime.datetime(2026, 9, 21, 12, 0, tzinfo=datetime.UTC)

    # Append t3, then t1, then t2
    buffer.append(t3, 1020.0)
    buffer.append(t1, 1000.0)
    buffer.append(t2, 1010.0)

    assert len(buffer) == 3
    # Check entries are strictly chronological
    entries = buffer.entries
    assert entries[0] == (t1, 1000.0)
    assert entries[1] == (t2, 1010.0)
    assert entries[2] == (t3, 1020.0)

    # Verify binary search lookup finds the closest
    assert buffer.get_pressure_at(t1) == 1000.0
    assert buffer.get_pressure_at(t2) == 1010.0
    assert buffer.get_pressure_at(t3) == 1020.0


def test_pressure_history_buffer_nearest_neighbor():
    """Test binary search chooses the closer point between predecessor and successor."""
    buffer = PressureHistoryBuffer()
    t_10 = datetime.datetime(2026, 9, 21, 10, 0, tzinfo=datetime.UTC)
    t_11 = datetime.datetime(2026, 9, 21, 11, 0, tzinfo=datetime.UTC)
    buffer.append(t_10, 1000.0)
    buffer.append(t_11, 1010.0)

    # 10:10 is closer to 10:00 (10m) than 11:00 (50m)
    t_10_10 = datetime.datetime(2026, 9, 21, 10, 10, tzinfo=datetime.UTC)
    assert buffer.get_pressure_at(t_10_10) == 1000.0

    # 10:50 is closer to 11:00 (10m) than 10:00 (50m)
    t_10_50 = datetime.datetime(2026, 9, 21, 10, 50, tzinfo=datetime.UTC)
    assert buffer.get_pressure_at(t_10_50) == 1010.0


def test_pressure_history_buffer_prune():
    """Test automatic pruning of entries exceeding max_age."""
    buffer = PressureHistoryBuffer(max_age=datetime.timedelta(hours=2))
    now = datetime.datetime(2026, 9, 21, 14, 0, tzinfo=datetime.UTC)

    buffer.append(now - datetime.timedelta(hours=3), 1000.0)  # should be pruned on next append
    buffer.append(now - datetime.timedelta(hours=1), 1010.0)
    buffer.append(now, 1020.0)

    assert len(buffer) == 2
    assert buffer.get_pressure_at(now - datetime.timedelta(hours=3)) is None
    assert buffer.get_pressure_at(now - datetime.timedelta(hours=1)) == 1010.0


def test_pressure_history_buffer_clear_and_empty():
    """Test clear method and empty buffer lookup."""
    buffer = PressureHistoryBuffer()
    now = datetime.datetime(2026, 9, 21, 14, 0, tzinfo=datetime.UTC)

    assert buffer.get_pressure_at(now) is None
    assert len(buffer) == 0

    buffer.append(now, 1013.0)
    assert len(buffer) == 1
    buffer.clear()
    assert len(buffer) == 0
    assert buffer.get_pressure_at(now) is None


def test_pressure_history_buffer_default_max_age():
    """Test buffer uses 25 hours as default max_age."""
    buffer = PressureHistoryBuffer()
    assert buffer.max_age == BUFFER_MAX_AGE


@pytest.mark.asyncio
async def test_async_get_history_pressures_batch_from_recorder_success():
    """Test single batch query retrieves multiple hours in one SQL call."""
    from unittest.mock import patch

    mock_hass = MagicMock()
    mock_recorder = MagicMock()

    now = datetime.datetime(2026, 9, 21, 14, 0, tzinfo=datetime.UTC)
    t_3h = now - datetime.timedelta(hours=3)
    t_6h = now - datetime.timedelta(hours=6)
    t_12h = now - datetime.timedelta(hours=12)

    s_12h = MagicMock(state="1005.0", last_changed=t_12h, attributes={"unit_of_measurement": "hPa"})
    s_6h = MagicMock(state="1010.0", last_changed=t_6h, attributes={"unit_of_measurement": "hPa"})
    s_3h = MagicMock(state="1015.0", last_changed=t_3h, attributes={"unit_of_measurement": "hPa"})

    mock_recorder.async_add_executor_job = AsyncMock(
        return_value={"sensor.pressure": [s_12h, s_6h, s_3h]}
    )

    buffer = PressureHistoryBuffer()
    with patch(
        "custom_components.zambretti_sager.history.get_instance", return_value=mock_recorder
    ):
        results = await async_get_history_pressures_batch_from_recorder(
            mock_hass,
            "sensor.pressure",
            [3, 6, 12],
            now,
            buffer=buffer,
        )

    # Verify only ONE executor job was scheduled (batch, not N+1)
    assert mock_recorder.async_add_executor_job.call_count == 1
    assert results[3] == 1015.0
    assert results[6] == 1010.0
    assert results[12] == 1005.0

    # Verify buffer was populated
    assert len(buffer) == 3
    assert buffer.get_pressure_at(t_3h) == 1015.0


@pytest.mark.asyncio
async def test_async_get_history_pressures_batch_empty_and_error():
    """Test batch query handling of empty hours and exceptions."""
    from unittest.mock import patch

    mock_hass = MagicMock()

    # Empty list returns empty dict with 0 jobs
    res = await async_get_history_pressures_batch_from_recorder(
        mock_hass, "sensor.pressure", [], datetime.datetime.now(datetime.UTC)
    )
    assert res == {}

    # Recorder failure returns {h: None} gracefully
    mock_recorder = MagicMock()
    mock_recorder.async_add_executor_job = AsyncMock(side_effect=RuntimeError("DB dead"))

    now = datetime.datetime.now(datetime.UTC)
    with patch(
        "custom_components.zambretti_sager.history.get_instance", return_value=mock_recorder
    ):
        res_err = await async_get_history_pressures_batch_from_recorder(
            mock_hass, "sensor.pressure", [3, 6], now
        )
    assert res_err == {3: None, 6: None}


@pytest.mark.asyncio
async def test_async_get_history_pressure_from_recorder_wrapper():
    """Test compatibility wrapper async_get_history_pressure_from_recorder."""
    from unittest.mock import patch

    mock_hass = MagicMock()
    mock_recorder = MagicMock()

    now = datetime.datetime(2026, 9, 21, 14, 0, tzinfo=datetime.UTC)
    t_3h = now - datetime.timedelta(hours=3)
    s_3h = MagicMock(state="1018.5", last_changed=t_3h, attributes={"unit_of_measurement": "hPa"})

    mock_recorder.async_add_executor_job = AsyncMock(return_value={"sensor.pressure": [s_3h]})

    with patch(
        "custom_components.zambretti_sager.history.get_instance", return_value=mock_recorder
    ):
        val = await async_get_history_pressure_from_recorder(mock_hass, "sensor.pressure", 3, now)
    assert val == 1018.5


@pytest.mark.asyncio
async def test_async_warm_history_buffer():
    """Test warming up buffer from recorder."""
    from unittest.mock import patch

    mock_hass = MagicMock()
    mock_recorder = MagicMock()

    now = datetime.datetime(2026, 9, 21, 14, 0, tzinfo=datetime.UTC)
    t_1h = now - datetime.timedelta(hours=1)
    s_1h = MagicMock(state="1013.0", last_changed=t_1h, attributes={"unit_of_measurement": "hPa"})

    mock_recorder.async_add_executor_job = AsyncMock(return_value={"sensor.pressure": [s_1h]})

    buffer = PressureHistoryBuffer()
    with patch(
        "custom_components.zambretti_sager.history.get_instance", return_value=mock_recorder
    ):
        loaded = await async_warm_history_buffer(mock_hass, "sensor.pressure", buffer, hours=2)
    assert loaded == 1
    assert len(buffer) == 1
    assert buffer.get_pressure_at(t_1h) == 1013.0
