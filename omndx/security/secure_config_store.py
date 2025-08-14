"""Encrypted configuration storage utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from . import encryption_utils as eu


class SecureConfigStore:
    """Persist configuration values encrypted on disk."""

    def __init__(self, path: str | Path, key: bytes) -> None:
        self.path = Path(path)
        self.key = key

    def write(self, data: Dict[str, Any]) -> None:
        """Encrypt and persist *data* to the configured path."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(data).encode()
        token = eu.encrypt(self.key, raw)
        self.path.write_bytes(token)

    def read(self) -> Dict[str, Any]:
        """Read and decrypt data from the configured path."""

        token = self.path.read_bytes()
        raw = eu.decrypt(self.key, token)
        return json.loads(raw.decode())


__all__ = ["SecureConfigStore"]

