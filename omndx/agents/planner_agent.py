"""Planner agent that delegates goal decomposition to :class:`SymbolicPlanner`.

TODO:
- Telemetry: track planning requests and durations.
- Metrics: analyze plan step counts and success rates.
- Security: validate goals to prevent harmful planning.
- Resiliency: implement fallback strategies for planning failures.
"""
from __future__ import annotations

from typing import List

from .agent_logger import AgentLogger
from omndx.core.symbolic_planner import SymbolicPlanner


class PlannerAgent:
    """High-level planning agent.

    The agent receives a user goal and returns an ordered list of actions using
    :class:`SymbolicPlanner`.  The implementation is intentionally lightweight
    but instrumented so downstream components can trace activity.
    """

    def __init__(self) -> None:
        self.logger = AgentLogger(self.__class__.__name__)
        self._planner = SymbolicPlanner()

    def run(self, goal: str) -> List[str]:
        """Return a plan for ``goal``."""
        self.logger.info("planning", tag="run")
        return self._planner.plan(goal)


__all__ = ["PlannerAgent"]
