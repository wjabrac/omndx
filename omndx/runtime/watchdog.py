"""Watchdog for monitoring and restarting agent tasks."""

from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, Dict

TaskFactory = Callable[[], Awaitable[None]]


class Watchdog:
    """Simple watchdog that restarts failing asynchronous tasks."""

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.loop = loop or asyncio.get_event_loop()
        self.logger = logger or logging.getLogger("omndx.watchdog")
        self._tasks: Dict[str, TaskFactory] = {}

    # ------------------------------------------------------------------
    def add_task(self, name: str, factory: TaskFactory) -> None:
        """Register a task *factory* under *name*."""

        self._tasks[name] = factory

    # ------------------------------------------------------------------
    async def _runner(self, name: str, factory: TaskFactory) -> None:
        while True:
            try:
                await factory()
                self.logger.info("Task %s completed", name)
                break
            except Exception:
                self.logger.exception("Task %s failed; restarting", name)

    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start all registered tasks under watchdog supervision."""

        for name, factory in self._tasks.items():
            self.loop.create_task(self._runner(name, factory))


__all__ = ["Watchdog"]
