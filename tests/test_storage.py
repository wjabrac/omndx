"""Tests for SQLite backed storage."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure package root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from omndx.storage import Storage


def test_storage_crud(tmp_path: Path) -> None:
    store = Storage(tmp_path / "test.sqlite")
    assert store.get("foo") is None
    store.set("foo", "bar")
    assert store.get("foo") == "bar"
    store.delete("foo")
    assert store.get("foo") is None
