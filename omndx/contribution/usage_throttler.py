"""Simple per-user usage throttler.

TODO:
- Telemetry: log throttled and allowed actions per user.
- Metrics: expose throttle hit rates.
- Security: guard against timestamp manipulation.
- Resiliency: persist state across restarts.
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, Tuple


class UsageThrottler:
    def __init__(self, interval: float, max_calls: int) -> None:
        self.interval = interval
        self.max_calls = max_calls
        self._history: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0.0))

    def allow(self, user: str) -> bool:
        count, timestamp = self._history[user]
        now = time.time()
        if now - timestamp > self.interval:
            self._history[user] = (1, now)
            return True
        if count < self.max_calls:
            self._history[user] = (count + 1, timestamp)
            return True
        return False


__all__ = ["UsageThrottler"]
