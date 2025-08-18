"""Tag-based tracking and logging utilities.

This module provides the :class:`TagLogger` which combines standard
logging with simple tag-style instrumentation. Each log entry can be
annotated with a tag that is counted in an internal metrics map.

The implementation favours resilience by guarding logging and tracking
operations. Failures in instrumentation should never raise exceptions
to calling code.
"""

from __future__ import annotations

from collections import defaultdict
import logging
from threading import Lock
from typing import Any, Dict


class TagLogger:
    """Logger supporting tag-style tracking.

    Parameters
    ----------
    component:
        Name of the component using this logger. It is used to create a
        namespaced logger instance.
    """

    def __init__(self, component: str) -> None:
        self.component = component
        self.logger = logging.getLogger(component)
        self.logger.setLevel(logging.INFO)

        # Initialise a default handler if no handlers are present.
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self._metrics: Dict[str, int] = defaultdict(int)
        self._lock = Lock()

    # ------------------------------------------------------------------
    # Tracking utilities
    # ------------------------------------------------------------------
    def track(self, tag: str) -> None:
        """Record a metric for *tag*.

        The method is thread-safe and resilient to internal errors.
        """

        try:
            with self._lock:
                self._metrics[tag] += 1
        except Exception:  # pragma: no cover - defensive safeguard
            self.logger.exception("Failed to track tag %s", tag)

    def get_metrics(self) -> Dict[str, int]:
        """Return a snapshot of the tracked metrics."""

        with self._lock:
            return dict(self._metrics)

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------
    def log(self, level: int, message: str, tag: str | None = None, **fields: Any) -> None:
        try:
            if fields:
                extras = " ".join(f"{k}={v}" for k, v in fields.items())
                message = f"{message} {extras}"
            if tag:
                message = f"[{tag}] {message}"
                self.track(tag)
            self.logger.log(level, message)
        except Exception:  # defensive
            self.logger.exception("Logging failure")

    def info(self, message: str, tag: str | None = None, **fields: Any) -> None:
        self.log(logging.INFO, message, tag, **fields)

    def warning(self, message: str, tag: str | None = None, **fields: Any) -> None:
        self.log(logging.WARNING, message, tag, **fields)

    def error(self, message: str, tag: str | None = None, **fields: Any) -> None:
        self.log(logging.ERROR, message, tag, **fields)


__all__ = ["TagLogger"]

