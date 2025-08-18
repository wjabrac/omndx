from __future__ import annotations

import pytest

from omndx.core.orchestrator import Orchestrator
from omndx.runtime.bootstrap import bootstrap
from omndx.runtime.metrics_collector import MetricsCollector, metrics
from omndx.runtime.test_harness import run_demo


def test_metrics_collector() -> None:
    collector = MetricsCollector()
    collector.record("efficiency", 1)
    collector.record("efficiency", 3, tags={"module": "test"})
    snapshot = collector.snapshot()
    assert snapshot["efficiency"] == 1
    assert snapshot["efficiency|module=test"] == 3
    with pytest.raises(ValueError):
        collector.record("bogus", 0)


def test_bootstrap_initialises_orchestrator(monkeypatch) -> None:
    messages: list[tuple[str, str]] = []

    class DummyLogger:
        def __init__(self, name: str) -> None:
            self.name = name

        def info(self, msg: str, /) -> None:
            messages.append((self.name, msg))

    monkeypatch.setattr("omndx.runtime.bootstrap.TagLogger", DummyLogger)
    orch = bootstrap()
    assert isinstance(orch, Orchestrator)
    assert messages == [("bootstrap", "initialising orchestrator")]


def test_orchestrator_run_records_metrics(monkeypatch) -> None:
    calls: list[str] = []

    def fake_record(category: str, value: float, tags: dict | None = None) -> None:  # noqa: D401
        calls.append(category)

    monkeypatch.setattr(metrics, "record", fake_record)
    orch = Orchestrator()
    with pytest.raises(NotImplementedError):
        orch.run([])
    assert set(calls) == {
        "reliability",
        "effectiveness",
        "cost",
        "efficiency",
    }


def test_run_demo(monkeypatch) -> None:
    monkeypatch.setattr(metrics, "record", lambda *a, **k: None)

    class DummyLogger:
        def __init__(self, *_: str) -> None:
            pass

        def info(self, *_: str) -> None:
            pass

    monkeypatch.setattr("omndx.runtime.bootstrap.TagLogger", DummyLogger)
    run_demo()
