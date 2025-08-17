"""Toy symmetric encryption utilities.

TODO:
- Telemetry: log encryption/decryption attempts without exposing keys.
- Metrics: measure cryptographic operation latency.
- Security: replace XOR scheme with proven algorithms.
- Resiliency: handle corrupted ciphertext and key rotation.
"""
from __future__ import annotations

import base64


def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encrypt(text: str, key: str) -> str:
    data = xor_bytes(text.encode(), key.encode())
    return base64.urlsafe_b64encode(data).decode()


def decrypt(token: str, key: str) -> str:
    data = base64.urlsafe_b64decode(token.encode())
    return xor_bytes(data, key.encode()).decode()


__all__ = ["encrypt", "decrypt"]
