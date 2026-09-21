"""History management: in-memory rolling buffer and recorder query adapters."""

from __future__ import annotations

import asyncio
import bisect
from collections.abc import Callable
import datetime
import logging

from homeassistant.components.recorder import get_instance, history
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .pressure_util import parse_pressure_hpa_from_history

_LOGGER = logging.getLogger(__name__)

BUFFER_MAX_AGE = datetime.timedelta(hours=25)
DEFAULT_TOLERANCE = datetime.timedelta(minutes=45)


class PressureHistoryBuffer:
    """In-memory rolling buffer of historical pressure readings with O(log N) lookups."""

    def __init__(self, max_age: datetime.timedelta = BUFFER_MAX_AGE) -> None:
        self.max_age = max_age
        self._buffer: list[tuple[datetime.datetime, float]] = []

    def append(self, timestamp: datetime.datetime, pressure_hpa: float) -> None:
        """Add a pressure reading maintaining chronological order and prune expired entries."""
        if not self._buffer or timestamp >= self._buffer[-1][0]:
            self._buffer.append((timestamp, pressure_hpa))
        else:
            bisect.insort(self._buffer, (timestamp, pressure_hpa), key=lambda x: x[0])
        self.prune(timestamp - self.max_age)

    def prune(self, cutoff: datetime.datetime) -> None:
        """Remove entries recorded before the cutoff timestamp in O(log N) time."""
        if not self._buffer:
            return
        idx = bisect.bisect_left(self._buffer, cutoff, key=lambda x: x[0])
        if idx > 0:
            del self._buffer[:idx]

    def get_pressure_at(
        self,
        target_time: datetime.datetime,
        tolerance: datetime.timedelta = DEFAULT_TOLERANCE,
    ) -> float | None:
        """Find the pressure reading closest to target_time within tolerance using binary search."""
        if not self._buffer:
            return None

        idx = bisect.bisect_left(self._buffer, target_time, key=lambda x: x[0])
        best_p: float | None = None
        best_diff = tolerance

        # Check predecessor (idx - 1)
        if idx > 0:
            t_prev, p_prev = self._buffer[idx - 1]
            diff_prev = abs(t_prev - target_time)
            if diff_prev <= best_diff:
                best_diff = diff_prev
                best_p = p_prev

        # Check candidate at insertion point (idx)
        if idx < len(self._buffer):
            t_next, p_next = self._buffer[idx]
            diff_next = abs(t_next - target_time)
            if diff_next <= best_diff:
                best_p = p_next

        return best_p

    def clear(self) -> None:
        """Clear all entries from the buffer."""
        self._buffer.clear()

    def __len__(self) -> int:
        return len(self._buffer)

    @property
    def entries(self) -> list[tuple[datetime.datetime, float]]:
        """Return a copy of entries in chronological order."""
        return list(self._buffer)


async def async_warm_history_buffer(
    hass: HomeAssistant,
    pressure_id: str,
    buffer: PressureHistoryBuffer,
    hours: int = 13,
    pressure_corrector: Callable[[float], float] | None = None,
) -> int:
    """Warm up the buffer with a single query to the recorder on startup.

    Returns the number of points loaded into the buffer.
    """
    now = dt_util.utcnow()
    start_time = now - datetime.timedelta(hours=hours)
    end_time = now
    loaded = 0

    try:
        events = await asyncio.wait_for(
            get_instance(hass).async_add_executor_job(
                history.get_significant_states,
                hass,
                start_time,
                end_time,
                [pressure_id],
            ),
            timeout=30.0,
        )
        if pressure_id in events and events[pressure_id]:
            for state in events[pressure_id]:
                t = getattr(state, "last_changed", getattr(state, "last_updated", None))
                if t is None:
                    continue
                try:
                    raw_p = parse_pressure_hpa_from_history(state)
                    p = pressure_corrector(raw_p) if pressure_corrector else raw_p
                    buffer.append(t, p)
                    loaded += 1
                except (ValueError, TypeError):
                    continue
            _LOGGER.debug("Warmed history buffer with %d points for %s", loaded, pressure_id)
    except Exception:
        _LOGGER.warning(
            "Could not warm pressure history from recorder for %s, will accumulate in memory",
            pressure_id,
        )

    return loaded


async def async_get_history_pressures_batch_from_recorder(
    hass: HomeAssistant,
    pressure_id: str,
    hours_list: list[int] | tuple[int, ...],
    now: datetime.datetime,
    window_minutes: int = 15,
    pressure_corrector: Callable[[float], float] | None = None,
    buffer: PressureHistoryBuffer | None = None,
) -> dict[int, float | None]:
    """Query recorder for pressure readings across multiple hours in a single batch query.

    Eliminates N+1 database queries by retrieving states over the full requested span
    in one SQL statement, then resolving the closest timestamp for each hour in memory.
    Optionally feeds retrieved points into the memory buffer.
    """
    if not hours_list:
        return {}

    max_hours = max(hours_list)
    window = datetime.timedelta(minutes=window_minutes)
    start_time = now - datetime.timedelta(hours=max_hours) - window
    end_time = now

    results: dict[int, float | None] = dict.fromkeys(hours_list)

    try:
        events = await asyncio.wait_for(
            get_instance(hass).async_add_executor_job(
                history.get_significant_states,
                hass,
                start_time,
                end_time,
                [pressure_id],
            ),
            timeout=30.0,
        )
        if pressure_id in events and events[pressure_id]:
            points: list[tuple[datetime.datetime, float]] = []
            for state in events[pressure_id]:
                t = getattr(state, "last_changed", getattr(state, "last_updated", None))
                if t is None:
                    continue
                try:
                    raw_p = parse_pressure_hpa_from_history(state)
                    p = pressure_corrector(raw_p) if pressure_corrector else raw_p
                    points.append((t, p))
                    if buffer is not None:
                        buffer.append(t, p)
                except (ValueError, TypeError):
                    continue

            # In-memory resolution for each requested hour using binary search
            if points:
                for h in hours_list:
                    target_time = now - datetime.timedelta(hours=h)
                    idx = bisect.bisect_left(points, target_time, key=lambda x: x[0])
                    best_p: float | None = None
                    best_diff = window

                    if idx > 0:
                        t_prev, p_prev = points[idx - 1]
                        diff_prev = abs(t_prev - target_time)
                        if diff_prev <= best_diff:
                            best_diff = diff_prev
                            best_p = p_prev

                    if idx < len(points):
                        t_next, p_next = points[idx]
                        diff_next = abs(t_next - target_time)
                        if diff_next <= best_diff:
                            best_p = p_next

                    results[h] = best_p
    except Exception:
        _LOGGER.exception(
            "Error fetching batch pressure history from recorder for %s (hours: %s)",
            pressure_id,
            hours_list,
        )

    return results


async def async_get_history_pressure_from_recorder(
    hass: HomeAssistant,
    pressure_id: str,
    hours: int,
    now: datetime.datetime,
    window_minutes: int = 15,
) -> float | None:
    """Query recorder for pressure reading N hours ago (compatibility wrapper)."""
    batch_res = await async_get_history_pressures_batch_from_recorder(
        hass, pressure_id, [hours], now, window_minutes=window_minutes
    )
    return batch_res.get(hours)
