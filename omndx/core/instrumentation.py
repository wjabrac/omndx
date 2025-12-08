"""Tag-based tracking and logging utilities.

This module provides the :class:`TagLogger` which combines standard
logging with simple tag-style instrumentation. Each log entry can be
annotated with a tag that is counted in an internal metrics map.

The implementation favours resilience by guarding logging and tracking
operations. Failures in instrumentation should never raise exceptions
to calling code.
"""

from __future__ import annotations

from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
import logging
from threading import Lock
from typing import Any, Dict, Mapping

from contextvars import ContextVar


@dataclass(frozen=True)
class TraceContext:
    """Lightweight trace context propagated across components.

    The context captures a stable trace identifier alongside optional span and
    parent identifiers.  Additional attributes provide structured metadata for
    log enrichment without forcing callers to create bespoke logging payloads.
    """

    trace_id: str
    span_id: str | None = None
    parent_span_id: str | None = None
    attributes: Mapping[str, Any] | None = None

    def as_fields(self) -> Dict[str, Any]:
        fields = {
            "trace_id": self.trace_id,
        }
        if self.span_id is not None:
            fields["span_id"] = self.span_id
        if self.parent_span_id is not None:
            fields["parent_span_id"] = self.parent_span_id
        if self.attributes:
            fields.update(self.attributes)
        return fields


_GLOBAL_TRACE: ContextVar[TraceContext | None] = ContextVar("omndx_trace", default=None)


class TagLogger:
    """Logger supporting tag-style tracking.

    Parameters
    ----------
    component:
        Name of the component using this logger. It is used to create a
        namespaced logger instance.
    """

    def __init__(self, component: str, *, context: TraceContext | None = None) -> None:
        self.component = component
        self.logger = logging.getLogger(component)
        self.logger.setLevel(logging.INFO)

        # Initialise a default handler if no handlers are present.
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        # Tracking state
        self._metrics: Dict[str, int] = defaultdict(int)
        self._lock = Lock()
        self._context: TraceContext | None = context

    # ------------------------------------------------------------------
    # Tracking utilities
    # ------------------------------------------------------------------
    def track(self, tag: str) -> None:
        """Record a metric for *tag*.

        The method is thread-safe and resilient to internal errors.
        """
        try:
            with self._lock:
                self._metrics[tag] += 1
        except Exception:  # defensive
            self.logger.exception("Failed to track tag %s", tag)

    def get_metrics(self) -> Dict[str, int]:
        """Return a snapshot of the tracked metrics."""
        with self._lock:
            return dict(self._metrics)

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------
    def log(
        self,
        level: int,
        message: str,
        tag: str | None = None,
        *,
        context: TraceContext | Mapping[str, Any] | None = None,
        **fields: Any,
    ) -> None:
        """Log *message* at *level* optionally associated with *tag*.

        When *tag* is supplied the metric counter for that tag is updated.
        Errors during logging are captured to avoid disrupting callers.
        """
        try:
            ctx = self._resolve_context(context)
            if fields:
                extras = " ".join(f"{k}={v}" for k, v in fields.items())
                message = f"{message} {extras}"
            if ctx:
                ctx_fields = " ".join(f"{k}={v}" for k, v in ctx.items())
                message = f"{message} {ctx_fields}".strip()
            if tag:
                message = f"[{tag}] {message}"
                self.track(tag)
            self.logger.log(level, message)
        except Exception:  # defensive
            self.logger.exception("Logging failure")

    def info(self, message: str, tag: str | None = None, **fields: Any) -> None:
        self.log(logging.INFO, message, tag, **fields)

    def warning(self, message: str, tag: str | None = None, **fields: Any) -> None:
        self.log(logging.WARNING, message, tag, **fields)

    def error(self, message: str, tag: str | None = None, **fields: Any) -> None:
        self.log(logging.ERROR, message, tag, **fields)

    @contextmanager
    def use_context(self, context: TraceContext) -> Any:
        """Temporarily bind a :class:`TraceContext` to the logger.

        The bound context participates in log enrichment and is also propagated
        to nested loggers via a global :class:`~contextvars.ContextVar` so that
        downstream components can inherit the trace identifiers.
        """

        token = _GLOBAL_TRACE.set(context)
        old = self._context
        self._context = context
        try:
            yield
        finally:
            self._context = old
            _GLOBAL_TRACE.reset(token)

    def _resolve_context(self, provided: TraceContext | Mapping[str, Any] | None) -> Dict[str, Any] | None:
        if provided is None:
            provided = self._context or _GLOBAL_TRACE.get()
        if provided is None:
            return None
        if isinstance(provided, TraceContext):
            return provided.as_fields()
        return dict(provided)


__all__ = ["TagLogger", "TraceContext"]
