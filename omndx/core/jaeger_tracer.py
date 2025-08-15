"""Jaeger tracing helpers."""
from __future__ import annotations

import contextlib
import logging
from typing import Optional

try:  # pragma: no cover - optional dependency
    from jaeger_client import Config
    import opentracing
except Exception:  # pragma: no cover - fallback when jaeger is absent
    Config = None  # type: ignore
    opentracing = None  # type: ignore

logger = logging.getLogger(__name__)


class JaegerTracer:
    """Small convenience wrapper around ``jaeger-client``."""

    def __init__(self, service_name: str = "omndx") -> None:
        self.tracer: Optional["opentracing.Tracer"] = None
        if Config:
            try:
                cfg = Config(
                    config={"sampler": {"type": "const", "param": 1}},
                    service_name=service_name,
                )
                self.tracer = cfg.initialize_tracer()
            except Exception:  # pragma: no cover - external service
                logger.warning("Jaeger tracer initialisation failed", exc_info=True)
        else:
            logger.warning("jaeger-client not installed; tracing disabled")

    @contextlib.contextmanager
    def span(self, name: str):
        """Context manager creating a span if tracing is enabled."""

        if not self.tracer:  # pragma: no cover - safety guard
            yield None
            return
        span = self.tracer.start_span(name)
        try:
            yield span
        finally:
            span.finish()


__all__ = ["JaegerTracer"]
