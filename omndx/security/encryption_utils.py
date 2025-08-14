"""Lightweight cryptographic helpers.

This module intentionally sticks to the Python standard library so that it
can operate in minimal environments without external dependencies.  The
helpers provided here are **not** intended for high security scenarios but
offer basic primitives that are sufficient for tests and demonstrations.

Functions
---------
``generate_key``
    Return a random key suitable for the helper functions.
``encrypt`` / ``decrypt``
    Symmetric XOR based transformation of byte strings.
``hash_data`` / ``verify_hash``
    SHA-256 based hashing with a random salt and constant time verification.
"""

from __future__ import annotations

import hmac
import os
import hashlib
from itertools import cycle
from typing import Tuple, Optional


def generate_key(length: int = 32) -> bytes:
    """Return a new random *length* byte key.

    Parameters
    ----------
    length:
        Size of the key in bytes.  Defaults to 32 bytes which is sufficient
        for the simple XOR based cipher below.
    """

    return os.urandom(length)


def encrypt(key: bytes, data: bytes) -> bytes:
    """Encrypt *data* using *key*.

    The implementation uses a repeated XOR stream which is symmetric – the
    same function can be used for decryption as well.  While this offers only
    very small security guarantees, it provides a deterministic transformation
    that suffices for testing and placeholder purposes.
    """

    return bytes(b ^ k for b, k in zip(data, cycle(key)))


def decrypt(key: bytes, token: bytes) -> bytes:
    """Decrypt *token* using *key*.

    Since the XOR operation is its own inverse this simply reuses
    :func:`encrypt`.
    """

    return encrypt(key, token)


def hash_data(data: bytes, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """Return a SHA-256 hash for *data* and the salt used.

    A random 16 byte salt is generated when one is not provided.  The digest is
    returned as raw bytes together with the salt so that callers can persist or
    later verify the hash.
    """

    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", data, salt, 100_000)
    return digest, salt


def verify_hash(data: bytes, digest: bytes, salt: bytes) -> bool:
    """Return ``True`` if *data* matches the given *digest*/*salt* pair."""

    new_digest, _ = hash_data(data, salt)
    return hmac.compare_digest(new_digest, digest)


__all__ = [
    "generate_key",
    "encrypt",
    "decrypt",
    "hash_data",
    "verify_hash",
]

