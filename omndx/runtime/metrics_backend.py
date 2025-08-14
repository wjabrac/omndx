"""SQLite backed metrics storage.

This module provides a minimal persistence layer for storing metric
increments together with the timestamp at which they were recorded.  The
backend is intentionally lightweight – it merely appends rows to a SQLite
database and offers a couple of convenience query helpers for tests and
simple reporting.

The storage schema is a single table named ``counters`` with the following
columns:

``name``
    Name of the metric/counter.

``value``
    Integer value to add to the counter.  Each flush from the collector is
    persisted as a separate row allowing for time series style analysis.

``ts``
    Unix timestamp (float) representing when the value was recorded.

The class defined here is purposely small – it creates connections on demand
and therefore is safe to use from multiple runs of the application.  The test
suite exercises a couple of typical reporting queries which can easily be
expanded upon by consumers of the module.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Dict, Optional


class MetricsBackend:
    """Persist metric counters to a SQLite database.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.  The parent directory must exist
        but the file itself will be created automatically if necessary.
    """

    def __init__(self, db_path: str | Path):
        self.path = Path(db_path)
        # Ensure the schema exists on initialisation so subsequent operations
        # can assume the table is present.
        self._ensure_schema()

    # ------------------------------------------------------------------
    # internal helpers
    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:  # type: sqlite3.Connection
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS counters (
                    name TEXT NOT NULL,
                    value INTEGER NOT NULL,
                    ts REAL NOT NULL
                )
                """
            )
            conn.commit()

    # ------------------------------------------------------------------
    # public API
    def record_counter(
        self, name: str, value: int, timestamp: Optional[float] = None
    ) -> None:
        """Record ``value`` for ``name`` at ``timestamp``.

        Each invocation appends a row to the ``counters`` table.  If
        ``timestamp`` is ``None`` the current time is used.
        """

        ts = float(time.time() if timestamp is None else timestamp)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO counters (name, value, ts) VALUES (?, ?, ?)",
                (name, int(value), ts),
            )
            conn.commit()

    def query_total(self, name: str, since: Optional[float] = None) -> int:
        """Return the total for ``name`` optionally filtering by ``since``.

        Parameters
        ----------
        name:
            Metric name to query.
        since:
            If provided, only values with a timestamp equal to or newer than
            ``since`` are considered.
        """

        with self._connect() as conn:
            if since is None:
                cur = conn.execute(
                    "SELECT COALESCE(SUM(value), 0) FROM counters WHERE name=?",
                    (name,),
                )
            else:
                cur = conn.execute(
                    """
                    SELECT COALESCE(SUM(value), 0)
                    FROM counters
                    WHERE name=? AND ts >= ?
                    """,
                    (name, since),
                )
            (total,) = cur.fetchone()
            return int(total or 0)

    def query_all(self, since: Optional[float] = None) -> Dict[str, int]:
        """Return totals for all counters as a ``dict``.

        ``since`` behaves like :meth:`query_total`.
        """

        with self._connect() as conn:
            if since is None:
                cur = conn.execute(
                    "SELECT name, SUM(value) FROM counters GROUP BY name"
                )
            else:
                cur = conn.execute(
                    """
                    SELECT name, SUM(value)
                    FROM counters
                    WHERE ts >= ?
                    GROUP BY name
                    """,
                    (since,),
                )
            return {name: int(total) for name, total in cur.fetchall()}


__all__ = ["MetricsBackend"]

