"""Agent-specific wrapper around :class:`~core.instrumentation.TagLogger`."""

from __future__ import annotations

from core.instrumentation import TagLogger


class AgentLogger(TagLogger):
    """Logger preconfigured for agent components."""

    def __init__(self, agent_name: str) -> None:
        super().__init__(agent_name)


__all__ = ["AgentLogger"]

