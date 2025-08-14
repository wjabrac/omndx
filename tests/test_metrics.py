"""Tests for metrics collection."""

from __future__ import annotations

import os
import sys

# Ensure package root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from omndx.runtime.metrics_collector import MetricsCollector


def test_metrics_collector_reports_values() -> None:
    collector = MetricsCollector()
    metrics = collector.get_metrics()
    assert "cpu_percent" in metrics
    assert "memory_mb" in metrics
    assert isinstance(metrics["cpu_percent"], float)
    assert isinstance(metrics["memory_mb"], float)
