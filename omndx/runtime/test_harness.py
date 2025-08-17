"""Simplistic test harness for manual experimentation.

TODO:
- Telemetry: record demo execution traces.
- Metrics: collect orchestrator run statistics.
- Security: isolate demo inputs from production data.
- Resiliency: provide cleanup on unexpected exceptions.
"""
from __future__ import annotations

from .bootstrap import bootstrap


def run_demo() -> None:
    orchestrator = bootstrap()
    try:
        orchestrator.run(["demo"])  # type: ignore[arg-type]
    except NotImplementedError:
        pass


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    run_demo()
