"""System metrics collection utilities.

The :class:`MetricsCollector` provides a minimal interface to gather
runtime metrics such as CPU and memory usage for the current process.
The implementation avoids external dependencies and uses :mod:`psutil`
if available, falling back to standard library facilities.
"""

from __future__ import annotations

import os
from typing import Dict

try:  # pragma: no cover - optional dependency
    import psutil  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - psutil may not be installed
    psutil = None  # type: ignore[assignment]


class MetricsCollector:
    """Collect basic CPU and memory metrics."""

    def __init__(self) -> None:
        if psutil:
            self._process = psutil.Process(os.getpid())
        else:  # pragma: no cover - platform specific
            self._process = None

    # ------------------------------------------------------------------
    def _cpu_percent(self) -> float:
        if self._process:
            try:
                return float(self._process.cpu_percent(interval=0.0))
            except Exception:  # pragma: no cover - defensive safeguard
                return 0.0
        return 0.0

    def _memory_mb(self) -> float:
        if self._process:
            try:
                return float(self._process.memory_info().rss) / (1024 * 1024)
            except Exception:  # pragma: no cover - defensive safeguard
                return 0.0
        try:  # pragma: no cover - fallback path
            import resource

            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        except Exception:
            return 0.0

    # ------------------------------------------------------------------
    def get_metrics(self) -> Dict[str, float]:
        """Return a snapshot of the current metrics."""

        return {
            "cpu_percent": self._cpu_percent(),
            "memory_mb": self._memory_mb(),
        }


__all__ = ["MetricsCollector"]
