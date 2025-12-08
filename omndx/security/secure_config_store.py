"""In-memory configuration store for secrets with auditing and replication."""
from __future__ import annotations

import threading
from typing import Dict, Iterable

from omndx.core.instrumentation import TagLogger, TraceContext
from omndx.runtime.metrics_collector import metrics

from .encryption_utils import decrypt, encrypt, rotate_key


class SecureConfigStore:
    def __init__(self, key: str, *, replicas: Iterable["SecureConfigStore"] | None = None) -> None:
        self._key = key
        self._data: Dict[str, str] = {}
        self._lock = threading.Lock()
        self._logger = TagLogger(self.__class__.__name__)
        self._replicas = list(replicas or [])

    def set(self, name: str, value: str, *, context: TraceContext | None = None) -> None:
        token = encrypt(value, self._key, context=context)
        with self._lock:
            self._data[name] = token
        self._logger.info("config set", tag="config_set", context=context, name=name)
        metrics.record("effectiveness", len(self._data), tags={"metric": "config_keys"})
        self._replicate("set", name, token, context=context)

    def get(self, name: str, *, context: TraceContext | None = None) -> str:
        with self._lock:
            token = self._data.get(name)
        if token is None:
            self._logger.warning("config missing", tag="config_miss", context=context, name=name)
            metrics.record("reliability", 0.0, tags={"metric": "config_hit_ratio"})
            raise KeyError(name)

        metrics.record("reliability", 1.0, tags={"metric": "config_hit_ratio"})
        return decrypt(token, self._key, context=context)

    def rotate(self, new_key: str, *, context: TraceContext | None = None, propagate: bool = True) -> None:
        """Re-encrypt stored values under ``new_key`` for key rotation."""

        with self._lock:
            for name, token in list(self._data.items()):
                self._data[name] = rotate_key(token, self._key, new_key, context=context)
            self._key = new_key
        self._logger.info("key rotated", tag="config_key_rotation", context=context)
        if propagate:
            self._replicate("rotate", None, new_key, context=context)

    def snapshot(self) -> Dict[str, str]:
        with self._lock:
            return dict(self._data)

    def load_snapshot(self, snapshot: Dict[str, str]) -> None:
        with self._lock:
            self._data = dict(snapshot)
        self._logger.info("snapshot loaded", tag="config_restore", size=len(snapshot))

    def _replicate(self, op: str, name: str | None, payload: str, *, context: TraceContext | None = None) -> None:
        for replica in self._replicas:
            try:
                if op == "set" and name is not None:
                    replica._ingest(name, payload, context=context)
                elif op == "rotate":
                    replica.rotate(payload, context=context, propagate=False)
            except Exception as exc:  # defensive, avoid cascading failures
                self._logger.error("replication failed", tag="config_replication_error", context=context, error=exc, replica=repr(replica))

    def _ingest(self, name: str, token: str, *, context: TraceContext | None = None) -> None:
        with self._lock:
            self._data[name] = token
        self._logger.info("replica updated", tag="config_replica", context=context, name=name)


__all__ = ["SecureConfigStore"]
