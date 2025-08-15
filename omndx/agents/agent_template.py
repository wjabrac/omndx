"""Skeleton agent implementation demonstrating instrumentation usage."""

from __future__ import annotations

from .agent_logger import AgentLogger


class Agent:
    """Base class for agents with built-in instrumentation."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.logger = AgentLogger(name)

    def perform(self) -> None:
        """Placeholder method representing agent work.

        Sub-classes should override this method. The default
        implementation simply logs the start and end of execution.
        """

        self.logger.info("Starting work", tag="start")
        try:
            # Actual agent logic would be placed here.
            pass
        except Exception as exc:  # pragma: no cover - placeholder logic
            self.logger.error(f"Failed with error: {exc}", tag="error")
        else:
            self.logger.info("Completed work", tag="end")


__all__ = ["Agent"]

