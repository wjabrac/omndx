"""Track user credit balances.

TODO:
- Telemetry: log credit adjustments and consumption.
- Metrics: monitor total credits and per-user usage.
- Security: persist balances securely and audit changes.
- Resiliency: ensure atomic updates and recovery from crashes.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict


class CreditTracker:
    def __init__(self) -> None:
        self._balances: Dict[str, int] = defaultdict(int)

    def add(self, user: str, amount: int) -> None:
        self._balances[user] += amount

    def consume(self, user: str, amount: int) -> bool:
        if self._balances[user] >= amount:
            self._balances[user] -= amount
            return True
        return False

    def balance(self, user: str) -> int:
        return self._balances[user]


__all__ = ["CreditTracker"]
