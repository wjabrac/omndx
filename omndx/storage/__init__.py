"""SQLite backed storage abstraction layer.

This module provides a tiny key/value store built on top of SQLite. It
exposes a :class:`Storage` class with simple CRUD operations and a
:func:`connect` helper returning a ready-to-use connection.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).with_name("state_store.sqlite")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS kv (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def connect(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Return a SQLite connection initialised with the schema."""

    conn = sqlite3.connect(str(db_path))
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


class Storage:
    """Simple key/value storage backed by SQLite."""

    def __init__(self, db_path: Path | str = DB_PATH) -> None:
        self.conn = connect(db_path)

    def set(self, key: str, value: str) -> None:
        """Insert or update *key* with *value*."""

        with self.conn:
            self.conn.execute(
                "REPLACE INTO kv (key, value) VALUES (?, ?)", (key, value)
            )

    def get(self, key: str) -> Optional[str]:
        """Retrieve the value for *key* or ``None`` when missing."""

        cur = self.conn.execute("SELECT value FROM kv WHERE key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else None

    def delete(self, key: str) -> None:
        """Remove *key* from the store."""

        with self.conn:
            self.conn.execute("DELETE FROM kv WHERE key = ?", (key,))


__all__ = ["Storage", "connect"]
