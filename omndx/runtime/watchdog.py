"""Asynchronous watchdog for periodic health checks.

The :class:`Watchdog` class provides a tiny utility that repeatedly invokes a
callback at a configurable interval.  It is intended for light‑weight health
checks or periodic housekeeping tasks inside the runtime environment.  The
callback may be either synchronous or asynchronous.
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Awaitable, Callable, Optional


Callback = Callable[[], Awaitable[None] | None]


class Watchdog:
    """Periodically trigger a callback on an event loop.

    Args:
        interval: Number of seconds to wait between callbacks.
        callback: The function to invoke periodically.  If the callback returns
            an awaitable it will be awaited before scheduling the next run.
    """

    def __init__(self, interval: float, callback: Callback) -> None:
        self._interval = float(interval)
        self._callback = callback
        self._task: Optional[asyncio.Task[None]] = None
        self._stopped = asyncio.Event()

    async def _run(self) -> None:
        """Internal task that schedules the callback."""

        try:
            while not self._stopped.is_set():
                await asyncio.sleep(self._interval)
                result = self._callback()
                if inspect.isawaitable(result):
                    await result  # type: ignore[arg-type]
        except asyncio.CancelledError:
            # Expected during shutdown; ignore.
            pass

    def start(self) -> None:
        """Start invoking the callback at the configured interval."""

        if self._task is not None:
            raise RuntimeError("Watchdog already running")
        loop = asyncio.get_running_loop()
        self._stopped.clear()
        self._task = loop.create_task(self._run())

    async def stop(self) -> None:
        """Cancel the watchdog and wait for the task to finish."""

        if self._task is None:
            return
        self._stopped.set()
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None


__all__ = ["Watchdog"]

