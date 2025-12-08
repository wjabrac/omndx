"""Track user credit balances with auditing and metrics."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import hmac
import json
import threading
import time
from typing import Dict, Iterable

from omndx.core.instrumentation import TagLogger, TraceContext
from omndx.runtime.metrics_collector import metrics


class CreditTracker:
    """Thread-safe tracker supporting audits and recovery."""

    def __init__(self, audit_key: str = "audit-secret") -> None:
        self._balances: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
        self._logger = TagLogger(self.__class__.__name__)
        self._audit_key = audit_key.encode()
        self._audit_log: list[dict[str, str | int | float]] = []
        self._last_digest: bytes | None = None

    # ------------------------------------------------------------------
    # Credits API
    # ------------------------------------------------------------------
    def add(self, user: str, amount: int, *, context: TraceContext | None = None) -> None:
        with self._lock:
            self._balances[user] += amount
            balance = self._balances[user]
            self._record_event("add", user, amount, balance)
        self._logger.info("credit added", tag="credit_add", context=context, user=user, amount=amount, balance=balance)
        metrics.record("effectiveness", balance, tags={"user": user, "metric": "balance"})

    def consume(self, user: str, amount: int, *, context: TraceContext | None = None) -> bool:
        with self._lock:
            if self._balances[user] >= amount:
                self._balances[user] -= amount
                balance = self._balances[user]
                self._record_event("consume", user, amount, balance)
                success = True
            else:
                balance = self._balances[user]
                success = False

        tag = "credit_consume_ok" if success else "credit_insufficient"
        self._logger.info("credit checked", tag=tag, context=context, user=user, amount=amount, balance=balance)
        metrics.record("reliability", 1.0 if success else 0.0, tags={"user": user, "metric": "consume"})
        return success

    def balance(self, user: str) -> int:
        with self._lock:
            return self._balances[user]

    # ------------------------------------------------------------------
    # Audit and durability helpers
    # ------------------------------------------------------------------
    def _record_event(self, action: str, user: str, amount: int, balance: int) -> None:
        event = {
            "action": action,
            "user": user,
            "amount": amount,
            "balance": balance,
            "ts": time.time(),
        }
        digest = hmac.new(self._audit_key, json.dumps(event, sort_keys=True).encode(), hashlib.sha256)
        if self._last_digest:
            digest.update(self._last_digest)
        signature = digest.digest()
        event["signature"] = digest.hexdigest()
        self._audit_log.append(event)
        self._last_digest = signature

    def export_state(self) -> dict[str, object]:
        """Return a serialisable snapshot for replication or persistence."""

        with self._lock:
            return {
                "balances": dict(self._balances),
                "audit_log": list(self._audit_log),
            }

    def load_state(self, state: dict[str, object]) -> None:
        """Restore balances from a previously exported snapshot."""

        with self._lock:
            balances = state.get("balances", {})
            if isinstance(balances, dict):
                self._balances = defaultdict(int, {k: int(v) for k, v in balances.items()})
            audit = state.get("audit_log", [])
            if isinstance(audit, Iterable):
                self._audit_log = list(audit)  # type: ignore[list-item]
                if self._audit_log:
                    try:
                        self._last_digest = bytes.fromhex(str(self._audit_log[-1].get("signature", "")))
                    except ValueError:
                        self._last_digest = None
            self._logger.info("state restored", tag="credit_state_restore", size=len(self._balances))


__all__ = ["CreditTracker"]
