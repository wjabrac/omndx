"""Compute basic trust scores from activity counts.

TODO:
- Telemetry: record trust score changes.
- Metrics: analyze distribution of scores.
- Security: prevent manipulation and ensure data integrity.
- Resiliency: persist scores to avoid loss on restart.
"""
from __future__ import annotations

from typing import Dict


class TrustScoreCalculator:
    def __init__(self) -> None:
        self._activity: Dict[str, int] = {}

    def record(self, user: str) -> None:
        self._activity[user] = self._activity.get(user, 0) + 1

    def score(self, user: str) -> float:
        count = self._activity.get(user, 0)
        return min(1.0, count / 10)


__all__ = ["TrustScoreCalculator"]
