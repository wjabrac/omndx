"""Gate access to LLM resources based on credits.

TODO:
- Telemetry: emit events for allowed and denied requests.
- Metrics: track credit consumption rates.
- Security: enforce user authentication and authorization.
- Resiliency: support fallback policies when tracker unavailable.
"""
from __future__ import annotations

from .credit_tracker import CreditTracker


class LlmAccessGate:
    def __init__(self, tracker: CreditTracker, cost: int = 1) -> None:
        self.tracker = tracker
        self.cost = cost

    def allow(self, user: str) -> bool:
        return self.tracker.consume(user, self.cost)


__all__ = ["LlmAccessGate"]
