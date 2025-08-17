"""Text repair agent performing simple normalisation.

TODO:
- Telemetry: log repair operations and anomalies.
- Metrics: measure correction counts and time.
- Security: prevent malicious escape sequences.
- Resiliency: support multi-language normalization strategies.
"""
from __future__ import annotations

from .agent_logger import AgentLogger


class RepairAgent:
    """Performs trivial text normalisation tasks."""

    def __init__(self) -> None:
        self.logger = AgentLogger(self.__class__.__name__)

    def run(self, text: str) -> str:
        """Return ``text`` with common whitespace issues fixed."""
        self.logger.info("repair", tag="run")
        return " ".join(text.split())


__all__ = ["RepairAgent"]
