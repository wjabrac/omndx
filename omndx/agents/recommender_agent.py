"""Minimal recommender agent producing placeholder suggestions.

TODO:
- Telemetry: track recommendation requests.
- Metrics: evaluate suggestion relevance.
- Security: filter inputs to prevent prompt injection.
- Resiliency: implement timeout and retry for external lookups.
"""
from __future__ import annotations

from typing import List

from .agent_logger import AgentLogger


class RecommenderAgent:
    """Return trivial recommendations for demonstration purposes."""

    def __init__(self) -> None:
        self.logger = AgentLogger(self.__class__.__name__)

    def run(self, item: str) -> List[str]:
        """Return a list with a single generic recommendation."""
        self.logger.info("recommending", tag="run")
        return [f"Consider exploring more about {item}."]


__all__ = ["RecommenderAgent"]
