"""Gate access to LLM resources based on credits with telemetry and fallbacks."""
from __future__ import annotations

from omndx.core.instrumentation import TagLogger, TraceContext
from omndx.runtime.metrics_collector import metrics

from .credit_tracker import CreditTracker


class LlmAccessGate:
    def __init__(self, tracker: CreditTracker, cost: int = 1, *, fail_open: bool = False) -> None:
        self.tracker = tracker
        self.cost = cost
        self.fail_open = fail_open
        self._logger = TagLogger(self.__class__.__name__)

    def allow(self, user: str, *, context: TraceContext | None = None) -> bool:
        if not user:
            self._logger.error("missing user", tag="access_denied", context=context)
            metrics.record("reliability", 0.0, tags={"metric": "access", "reason": "missing_user"})
            return False

        try:
            allowed = self.tracker.consume(user, self.cost, context=context)
        except Exception as exc:  # defensive: tracker down or corrupted
            self._logger.error("tracker failure", tag="tracker_error", context=context, error=exc)
            metrics.record("reliability", 0.0, tags={"metric": "access", "reason": "tracker_error"})
            allowed = self.fail_open

        tag = "access_granted" if allowed else "access_denied"
        self._logger.info("llm access evaluated", tag=tag, context=context, user=user, cost=self.cost)
        metrics.record("effectiveness", 1.0 if allowed else 0.0, tags={"metric": "access", "user": user})
        return allowed


__all__ = ["LlmAccessGate"]
