from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import List, Optional, Any

from omndx.storage.chat_memory import ChatMemory

from .core_agent import CoreAgent
from .llm_local import LLM


@dataclass
class PlannerAgent:
    llm: LLM
    memory: ChatMemory | None = None
    name: str = "planner"
    description: str = "Create ordered plans for a goal"

    def __post_init__(self) -> None:
        self._core = CoreAgent(self.llm, stop=["\n\n"])

    def plan(
        self,
        goal: str,
        as_json: bool = False,
        max_steps: Optional[int] = 12,
        session_id: Optional[str] = None,
        context_window: int = 5,
    ) -> List[str] | str:
        prompt = f"Return an ordered, concise list of steps for the goal.\nGoal: {goal}\nOutput:\n1. "
        if self.memory and session_id:
            ctx = self.memory.get_recent_context(session_id, context_window)
            if ctx:
                prompt = f"Context:\n{ctx}\n\n" + prompt
            self.memory.add_message(session_id, "user", f"Goal: {goal}")
        raw = self._core.run(prompt)
        if self.memory and session_id:
            self.memory.add_message(session_id, "assistant", raw)
        lines = [
            re.sub(r"^\s*\d+[\).\-\:]*\s*", "", ln).strip(" -*")
            for ln in raw.splitlines()
            if ln.strip()
        ]
        if max_steps is not None:
            lines = lines[:max_steps]
        return json.dumps(lines) if as_json else lines

    def run(self, **kwargs: Any) -> Any:
        return self.plan(kwargs.get("goal", ""), **{k: v for k, v in kwargs.items() if k != "goal"})


__all__ = ["PlannerAgent"]
