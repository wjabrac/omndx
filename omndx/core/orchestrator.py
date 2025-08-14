"""Simple orchestration of tasks across agents."""

from __future__ import annotations

from typing import Any, Dict

from .agent_router import AgentRouter
from .task_registry import TaskRegistry


class Orchestrator:
    """Coordinates task execution via a router and registry."""

    def __init__(self, router: AgentRouter, registry: TaskRegistry):
        self.router = router
        self.registry = registry

    # ------------------------------------------------------------------
    def run(self) -> Dict[int, Any]:
        """Execute all tasks in the registry and return results."""

        results: Dict[int, Any] = {}
        for task_id, task in self.registry.all().items():
            results[task_id] = self.router.route(task)
        return results


__all__ = ["Orchestrator"]
