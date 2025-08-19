from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import List, Any, Optional

from omndx.storage.chat_memory import ChatMemory

from .core_agent import CoreAgent
from .llm_local import LLM

_SYSTEM_PROMPT = (
    "You are a recommendation assistant. Provide bullet list items and no"
    " additional commentary."
)


@dataclass
class RecommenderAgent:
    llm: LLM
    memory: ChatMemory | None = None
    name: str = "recommender"
    description: str = "Recommend items based on a request"

    def __post_init__(self) -> None:
        self._core = CoreAgent(self.llm, stop=["\n\n"])

    def recommend(
        self,
        request: str,
        as_json: bool = False,
        max_items: Optional[int] = 5,
        session_id: Optional[str] = None,
        context_window: int = 5,
    ) -> List[str] | str:
        prompt = f"{_SYSTEM_PROMPT}\nRequest: {request}\nRecommendations:\n- "
        if self.memory and session_id:
            ctx = self.memory.get_recent_context(session_id, context_window)
            if ctx:
                prompt = f"Context:\n{ctx}\n\n" + prompt
            self.memory.add_message(session_id, "user", request)
        raw = self._core.run(prompt)
        if self.memory and session_id:
            self.memory.add_message(session_id, "assistant", raw)
        raw = re.sub(r"(?i)system:.*", "", raw)
        lines = [
            re.sub(r"^\s*[-*\d.]+\s*", "", ln).strip()
            for ln in raw.splitlines()
            if ln.strip()
        ]
        cleaned = [ln for ln in lines if not re.search(r"(?i)(system|assistant|user):", ln)]
        if max_items is not None:
            cleaned = cleaned[:max_items]
        return json.dumps(cleaned) if as_json else cleaned

    def run(self, **kwargs: Any) -> Any:
        return self.recommend(
            kwargs.get("request", ""),
            **{k: v for k, v in kwargs.items() if k != "request"}
        )


__all__ = ["RecommenderAgent"]
