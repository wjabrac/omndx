from __future__ import annotations

import os

from .llm_local import LangChainLLM, LLM, FakeListLLM
from .planner_agent import PlannerAgent
from .tagger_agent import TaggerAgent
from .recommender_agent import RecommenderAgent
from omndx.storage.chat_memory import ChatMemory


def build_default_agents(llm: LLM | None = None, memory: ChatMemory | None = None):
    """Return default agent instances wired to a usable LLM."""

    if llm is None:
        try:
            cfg = {"model_name": os.getenv("OMNDX_MODEL", "gpt-3.5-turbo")}
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                cfg["api_key"] = api_key
            llm = LangChainLLM(cfg)
        except Exception:
            # fall back to deterministic fake that returns a non-empty string
            llm = FakeListLLM(["ok"])
    return {
        "planner": PlannerAgent(llm, memory=memory),
        "tagger": TaggerAgent(llm, memory=memory),
        "recommender": RecommenderAgent(llm, memory=memory),
    }


__all__ = ["build_default_agents"]
