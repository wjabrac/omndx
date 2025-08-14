"""Tests for agent creation, routing and orchestration."""

from __future__ import annotations

import os
import sys
from typing import Any, Dict

# Ensure package root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from omndx.core import AgentForge, AgentRouter, Orchestrator, TaskRegistry


class EchoAgent:
    """Agent that echoes a payload with a prefix."""

    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix

    def handle(self, task: Dict[str, Any]) -> str:
        return f"{self.prefix}{task['payload']}"


class MultiplyAgent:
    """Agent that multiplies a numeric payload."""

    def __init__(self, factor: int) -> None:
        self.factor = factor

    def handle(self, task: Dict[str, Any]) -> int:
        return task["payload"] * self.factor


def _agent_path(cls: type) -> str:
    return f"{cls.__module__}.{cls.__name__}"


def test_agent_forge_creates_instances() -> None:
    config = {
        "echo": {"path": _agent_path(EchoAgent), "params": {"prefix": "hi:"}},
    }
    forge = AgentForge(config)
    agent = forge.get_agent("echo")
    assert agent.handle({"payload": "there"}) == "hi:there"


def test_agent_router_routes_to_correct_agent() -> None:
    config = {
        "echo": {"path": _agent_path(EchoAgent), "params": {"prefix": ""}},
        "mul": {"path": _agent_path(MultiplyAgent), "params": {"factor": 2}},
    }
    forge = AgentForge(config)
    router = AgentRouter(forge, {"echo": "echo", "multiply": "mul"})

    assert router.route({"type": "echo", "payload": "A"}) == "A"
    assert router.route({"type": "multiply", "payload": 5}) == 10


def test_orchestrator_runs_tasks() -> None:
    config = {
        "echo": {"path": _agent_path(EchoAgent), "params": {"prefix": "!"}},
        "mul": {"path": _agent_path(MultiplyAgent), "params": {"factor": 3}},
    }
    forge = AgentForge(config)
    router = AgentRouter(forge, {"echo": "echo", "multiply": "mul"})
    registry = TaskRegistry()
    t1 = registry.create({"type": "echo", "payload": "x"})
    t2 = registry.create({"type": "multiply", "payload": 4})

    orchestrator = Orchestrator(router, registry)
    results = orchestrator.run()

    assert results[t1] == "!x"
    assert results[t2] == 12


def test_task_registry_crud_operations() -> None:
    registry = TaskRegistry()
    task_id = registry.create({"type": "echo", "payload": "data"})
    assert registry.read(task_id)["payload"] == "data"

    registry.update(task_id, {"payload": "new"})
    assert registry.read(task_id)["payload"] == "new"

    registry.delete(task_id)
    assert registry.all() == {}
