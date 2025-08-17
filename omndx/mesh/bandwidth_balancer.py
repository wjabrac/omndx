"""Naive bandwidth balancer using a token bucket.

TODO:
- Telemetry: record token consumption events.
- Metrics: expose allowed/denied request counts.
- Security: validate peer identities before balancing.
- Resiliency: persist state for crash recovery.
"""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class BandwidthBalancer:
    capacity: int
    refill_rate: float
    tokens: float = 0
    timestamp: float = time.time()

    def allow(self, amount: int) -> bool:
        now = time.time()
        elapsed = now - self.timestamp
        self.timestamp = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


__all__ = ["BandwidthBalancer"]
