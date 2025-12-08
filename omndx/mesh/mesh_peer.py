"""Peer representation for the experimental mesh network with safety guards."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from omndx.core.instrumentation import TagLogger, TraceContext
from omndx.runtime.metrics_collector import metrics
from omndx.security.encryption_utils import decrypt, encrypt


@dataclass
class MeshPeer:
    """Peer containing identity, buffer and optional shared secret."""

    peer_id: str
    inbox: list[dict[str, Any]] = field(default_factory=list)
    shared_key: str | None = None
    online: bool = True
    _logger: TagLogger = field(init=False, repr=False)

    def __post_init__(self) -> None:  # pragma: no cover - trivial setup
        object.__setattr__(self, "_logger", TagLogger(self.__class__.__name__))

    def send(self, other: "MeshPeer", message: str, *, context: TraceContext | None = None) -> bool:
        start = time.perf_counter()
        if not other.online:
            self._logger.warning("peer offline", tag="mesh_offline", context=context, peer=other.peer_id)
            metrics.record("reliability", 0.0, tags={"metric": "mesh_send", "peer": other.peer_id})
            return False

        payload = self._prepare_payload(message)
        other.inbox.append({"from": self.peer_id, **payload})

        elapsed = time.perf_counter() - start
        self._logger.info("message sent", tag="mesh_send", context=context, peer=other.peer_id, elapsed=elapsed)
        metrics.record("efficiency", elapsed, tags={"metric": "mesh_latency", "peer": other.peer_id})
        metrics.record("effectiveness", len(message), tags={"metric": "mesh_bytes"})
        return True

    def receive(self, *, context: TraceContext | None = None) -> List[str]:
        messages: List[str] = []
        while self.inbox:
            envelope = self.inbox.pop(0)
            try:
                messages.append(self._unwrap_payload(envelope))
                metrics.record("reliability", 1.0, tags={"metric": "mesh_receive"})
            except Exception as exc:  # defensive: drop corrupted payloads
                self._logger.error("payload error", tag="mesh_receive_error", context=context, error=exc)
                metrics.record("reliability", 0.0, tags={"metric": "mesh_receive"})
        return messages

    def _prepare_payload(self, message: str) -> Dict[str, Any]:
        ts = time.time()
        if self.shared_key:
            cipher = encrypt(message, self.shared_key)
            return {"cipher": cipher, "ts": ts, "encrypted": True}
        return {"message": message, "ts": ts, "encrypted": False}

    def _unwrap_payload(self, payload: Dict[str, Any]) -> str:
        if payload.get("encrypted"):
            if not self.shared_key:
                raise RuntimeError("missing shared key for encrypted payload")
            return decrypt(str(payload["cipher"]), self.shared_key)
        return str(payload.get("message", ""))


__all__ = ["MeshPeer"]
