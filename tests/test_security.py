"""Tests for security helpers."""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path

import pytest

# Ensure the package root is on the import path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from omndx.security import (
    adult_content_filter,
    encryption_utils,
    sandbox_policy,
    secure_config_store,
)


def test_encryption_round_trip() -> None:
    key = encryption_utils.generate_key()
    message = b"secret message"
    encrypted = encryption_utils.encrypt(key, message)
    assert encrypted != message
    decrypted = encryption_utils.decrypt(key, encrypted)
    assert decrypted == message


def test_hash_and_verify() -> None:
    data = b"important"
    digest, salt = encryption_utils.hash_data(data)
    assert encryption_utils.verify_hash(data, digest, salt)
    assert not encryption_utils.verify_hash(b"tampered", digest, salt)


def test_secure_config_store_roundtrip(tmp_path: Path) -> None:
    key = encryption_utils.generate_key()
    store_path = tmp_path / "config.sec"
    store = secure_config_store.SecureConfigStore(store_path, key)
    store.write({"token": "abc"})
    # ensure raw file does not contain plaintext
    assert "abc" not in store_path.read_text(errors="ignore")
    assert store.read()["token"] == "abc"


def test_sandbox_policy_blocks_file_and_network(tmp_path: Path) -> None:
    with sandbox_policy.SandboxPolicy():
        with pytest.raises(PermissionError):
            open(tmp_path / "blocked.txt", "w")
        with pytest.raises(PermissionError):
            socket.socket()


def test_adult_content_filter() -> None:
    flt = adult_content_filter.AdultContentFilter()
    assert flt.is_safe("wholesome text")
    assert not flt.is_safe("this contains porn references")

