"""In process metrics collection utilities.

The :class:`MetricsCollector` class collects counter increments in memory and
flushes them to a persistence backend.  The backend is intentionally abstract
and only requires a ``record_counter`` method which accepts ``name``, ``value``
and ``timestamp`` arguments.  This mirrors the interface of
``MetricsBackend`` defined in :mod:`metrics_backend` but allows alternative
implementations for testing.

Typical usage::

    backend = MetricsBackend("/tmp/metrics.db")
    collector = MetricsCollector(backend)

    collector.increment("requests")
    collector.increment("requests", 2)
    collector.flush()  # persists the values to the database

The ``flush`` method is explicit so callers can control when the database is
written to.  This keeps the overhead of instrumentation low while still
allowing the caller to persist metrics periodically or at shutdown.
"""

from __future__ import annotations

import time
from collections import Counter
from typing import MutableMapping, Protocol


class MetricsBackendProtocol(Protocol):
    """Protocol describing the backend expected by :class:`MetricsCollector`."""

    def record_counter(self, name: str, value: int, timestamp: float | None = None) -> None:  # pragma: no cover - protocol definition
        ...


class MetricsCollector:
    """Collect and persist metric counters."""

    def __init__(self, backend: MetricsBackendProtocol):
        self._backend = backend
        self._counters: MutableMapping[str, int] = Counter()

    # ------------------------------------------------------------------
    def increment(self, name: str, amount: int = 1) -> None:
        """Increment ``name`` by ``amount`` in memory.

        The values are not persisted until :meth:`flush` is invoked.
        """

        self._counters[name] += int(amount)

    # ------------------------------------------------------------------
    def flush(self) -> None:
        """Write all collected counters to the backend.

        After flushing the in-memory counters are cleared.  A single timestamp
        is used for all metrics recorded in a given flush to simplify
        aggregation downstream.
        """

        if not self._counters:
            return

        ts = time.time()
        for name, value in list(self._counters.items()):
            if value:
                self._backend.record_counter(name, value, ts)

        self._counters.clear()


__all__ = ["MetricsCollector"]

