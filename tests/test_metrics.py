"""Integration tests for the metrics backend and collector."""

from __future__ import annotations

import time
from pathlib import Path
import sys

# Ensure the project root (containing the ``omndx`` package) is on ``sys.path``
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from omndx.runtime.metrics_backend import MetricsBackend
from omndx.runtime.metrics_collector import MetricsCollector


def test_persistence_across_runs(tmp_path: Path) -> None:
    db = tmp_path / "metrics.db"

    # First "run" of the application
    backend1 = MetricsBackend(db)
    collector1 = MetricsCollector(backend1)
    collector1.increment("requests", 5)
    collector1.flush()

    # Second run should see the persisted values
    backend2 = MetricsBackend(db)
    assert backend2.query_total("requests") == 5

    # Adding more data should accumulate
    collector2 = MetricsCollector(backend2)
    collector2.increment("requests", 3)
    collector2.flush()

    assert backend2.query_total("requests") == 8


def test_reporting_queries(tmp_path: Path) -> None:
    db = tmp_path / "metrics.db"
    backend = MetricsBackend(db)
    collector = MetricsCollector(backend)

    collector.increment("foo", 2)
    collector.increment("bar")
    collector.flush()

    # Basic query for all counters
    assert backend.query_all() == {"foo": 2, "bar": 1}

    # Querying with a timestamp should only include recent data
    checkpoint = time.time()
    collector.increment("foo", 1)
    collector.flush()

    assert backend.query_total("foo", since=checkpoint) == 1
    assert backend.query_all(since=checkpoint) == {"foo": 1}

