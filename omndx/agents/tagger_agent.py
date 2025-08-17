"""Simple tag extraction agent.

TODO:
- Telemetry: track tagging requests and outcomes.
- Metrics: measure tag extraction performance.
- Security: sanitize input text to avoid injections.
- Resiliency: handle extremely large documents gracefully.
"""
from __future__ import annotations

from typing import List

from .agent_logger import AgentLogger


class TaggerAgent:
    """Extracts naive keyword tags from text."""

    def __init__(self) -> None:
        self.logger = AgentLogger(self.__class__.__name__)

    def run(self, text: str) -> List[str]:
        """Return unique lowercase words from ``text``."""
        self.logger.info("tagging", tag="run")
        words = {w.strip(".,!?").lower() for w in text.split() if w}
        return sorted(words)


__all__ = ["TaggerAgent"]
