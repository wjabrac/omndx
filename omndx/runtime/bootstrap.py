"""Runtime bootstrap helpers.

TODO:
- Telemetry: emit startup and shutdown events.
- Metrics: measure bootstrap duration and orchestrator health.
- Security: load configuration from secure sources.
- Resiliency: support restart strategies on failure.
"""
from __future__ import annotations

from omndx.core.orchestrator import Orchestrator
from omndx.core.instrumentation import TagLogger


def bootstrap() -> Orchestrator:
    """Initialise logging and return an :class:`Orchestrator` instance."""
    logger = TagLogger("bootstrap")
    logger.info("initialising orchestrator")
    return Orchestrator()


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    bootstrap()
