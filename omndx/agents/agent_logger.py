from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from omndx.core.instrumentation import TagLogger


class AgentLogger(TagLogger):
    """Structured logger with context binding built atop :class:`TagLogger`."""

    def __init__(
        self,
        name: str = "omndx.agent",
        context: Optional[Dict[str, Any]] = None,
        **kw: Any,
    ) -> None:
        super().__init__(kw.pop("agent_name", name))
        self._context: Dict[str, Any] = dict(context or {})

    def bind(self, **ctx: Any) -> None:
        """Attach persistent context to all emitted logs."""
        self._context.update(ctx)

    def _merge(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {**self._context, **(context or {})}

    def _emit(self, level: int, event: str, context: Optional[Dict[str, Any]]) -> None:
        ctx = self._merge(context)
        msg = f"{event} {ctx}" if ctx else event
        super().log(level, msg, event)

    def debug(self, event: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._emit(logging.DEBUG, event, context)

    def info(self, event: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._emit(logging.INFO, event, context)

    def warning(self, event: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._emit(logging.WARNING, event, context)

    def error(self, event: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._emit(logging.ERROR, event, context)


__all__ = ["AgentLogger"]
