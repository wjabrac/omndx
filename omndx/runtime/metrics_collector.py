"""Centralised metrics collection for the OMNDX platform.

This module provides a lightweight, tag-driven metrics system focused on the
key operational dimensions of reliability, effectiveness, efficiency, and
cost.  Metrics are stored in-memory and also emitted via standard logging so
that external monitoring systems can aggregate them in real time.
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from typing import Any, Dict


class MetricsCollector:
    """Collects and aggregates metrics with optional tags.

    The collector maintains per-metric lists of observed values. Each metric is
    addressed by a category (e.g. ``"efficiency"``) and an optional tag set that
    provides context such as ``{"module": "AgentRouter"}``.
    """

    _VALID_CATEGORIES = {"reliability", "effectiveness", "efficiency", "cost"}

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._values: Dict[str, list[float]] = defaultdict(list)
        self._logger = logging.getLogger("omndx.metrics")
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s %(message)s")
            )
            self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

    def record(self, category: str, value: float, tags: Dict[str, Any] | None = None) -> None:
        """Record a metric value under ``category`` with optional ``tags``.

        Args:
            category: One of ``reliability``, ``effectiveness``, ``efficiency``,
                or ``cost``.
            value: Numerical value associated with the observation.
            tags: Optional dictionary of tag keys and values to provide context.
        """
        if category not in self._VALID_CATEGORIES:
            raise ValueError(f"invalid metric category: {category}")
        key = self._tag_key(category, tags)
        with self._lock:
            self._values[key].append(float(value))
        self._logger.info(
            "metric", extra={"metric": category, "value": value, "tags": tags or {}}
        )

    def snapshot(self) -> Dict[str, float]:
        """Return the average value for each recorded metric key."""
        with self._lock:
            return {k: sum(v) / len(v) for k, v in self._values.items() if v}

    @staticmethod
    def _tag_key(category: str, tags: Dict[str, Any] | None) -> str:
        if not tags:
            return category
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{category}|{tag_str}"


# Global collector instance used across the platform.
metrics = MetricsCollector()
