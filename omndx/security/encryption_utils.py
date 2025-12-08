"""Telemetry-friendly symmetric encryption utilities."""
from __future__ import annotations

import base64
import time

from omndx.core.instrumentation import TagLogger, TraceContext
from omndx.runtime.metrics_collector import metrics


_LOGGER = TagLogger("encryption")


def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encrypt(text: str, key: str, *, context: TraceContext | None = None) -> str:
    start = time.perf_counter()
    data = xor_bytes(text.encode(), key.encode())
    token = base64.urlsafe_b64encode(data).decode()
    elapsed = time.perf_counter() - start
    _LOGGER.info("encrypt", tag="encrypt", context=context, size=len(text), elapsed=elapsed)
    metrics.record("efficiency", elapsed, tags={"metric": "encrypt"})
    return token


def decrypt(token: str, key: str, *, context: TraceContext | None = None) -> str:
    start = time.perf_counter()
    try:
        data = base64.urlsafe_b64decode(token.encode())
        text = xor_bytes(data, key.encode()).decode()
    except Exception as exc:  # defensive against corrupted payloads
        _LOGGER.error("decrypt failed", tag="decrypt_error", context=context, error=exc)
        metrics.record("reliability", 0.0, tags={"metric": "decrypt"})
        raise
    else:
        elapsed = time.perf_counter() - start
        _LOGGER.info("decrypt", tag="decrypt", context=context, size=len(text), elapsed=elapsed)
        metrics.record("efficiency", elapsed, tags={"metric": "decrypt"})
        return text


def rotate_key(token: str, old_key: str, new_key: str, *, context: TraceContext | None = None) -> str:
    """Re-encrypt ``token`` using ``new_key`` to support key rotation."""

    plaintext = decrypt(token, old_key, context=context)
    return encrypt(plaintext, new_key, context=context)


__all__ = ["encrypt", "decrypt"]
