"""Utilities for streaming logs to user interfaces."""

from __future__ import annotations

import logging
from queue import Queue
from typing import Iterator

from ..core import TagLogger


class _QueueHandler(logging.Handler):
    """Small logging handler that pushes formatted records onto a queue."""

    def __init__(self, queue: Queue[str]) -> None:
        super().__init__()
        self.queue = queue
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - thin
        self.queue.put(self.format(record))


class LogStreamer:
    """Attach to a :class:`TagLogger` and yield log messages as they occur."""

    def __init__(self, logger: TagLogger) -> None:
        self._queue: Queue[str] = Queue()
        self._handler = _QueueHandler(self._queue)
        logger.logger.addHandler(self._handler)
        self.logger = logger

    def stream(self) -> Iterator[str]:
        """Yield log lines as they are emitted."""

        while True:
            yield self._queue.get()

    def close(self) -> None:
        """Detach the handler from the logger."""  # pragma: no cover - trivial

        self.logger.logger.removeHandler(self._handler)


__all__ = ["LogStreamer"]

