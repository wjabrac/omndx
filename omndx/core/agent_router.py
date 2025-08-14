"""Task routing to agent instances."""

from __future__ import annotations

from typing import Any, Mapping

from .agent_forge import AgentForge


class AgentRouter:
    """Router that directs tasks to agents based on task type."""

    def __init__(self, forge: AgentForge, routes: Mapping[str, str]):
        self.forge = forge
        self.routes = dict(routes)

    # ------------------------------------------------------------------
    def route(self, task: Mapping[str, Any]) -> Any:
        """Dispatch *task* to the appropriate agent and return the result."""

        task_type = task.get("type")
        if task_type not in self.routes:
            raise KeyError(f"No route for task type '{task_type}'")
        agent_name = self.routes[task_type]
        agent = self.forge.get_agent(agent_name)
        handler = getattr(agent, "handle")
        return handler(task)


__all__ = ["AgentRouter"]
