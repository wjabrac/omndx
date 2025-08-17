"""In-memory configuration store for secrets.

TODO:
- Telemetry: track configuration access patterns.
- Metrics: expose cache hit ratios and key counts.
- Security: persist encrypted data and support key rotation.
- Resiliency: replicate store for high availability.
"""
from __future__ import annotations

from typing import Dict

from .encryption_utils import decrypt, encrypt


class SecureConfigStore:
    def __init__(self, key: str) -> None:
        self._key = key
        self._data: Dict[str, str] = {}

    def set(self, name: str, value: str) -> None:
        self._data[name] = encrypt(value, self._key)

    def get(self, name: str) -> str:
        token = self._data[name]
        return decrypt(token, self._key)


__all__ = ["SecureConfigStore"]
