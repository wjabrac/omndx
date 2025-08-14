"""Core agent abstraction.

The :class:`CoreAgent` is intentionally lightweight.  It accepts any object
implementing the :class:`~omndx.agents.llm_local.LLM` protocol and delegates
text generation to it.  The purpose of the class is to provide a single place
where different LLM implementations can be plugged in, allowing tests to use a
simple echo model or a LangChain powered one.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .llm_local import LLM


@dataclass
class CoreAgent:
    """Minimal core agent that relies on an injected LLM instance."""

    llm: LLM

    def run(self, prompt: str, **kwargs: Any) -> str:
        """Return the LLM's response for ``prompt``.

        Additional ``kwargs`` are forwarded to the underlying LLM's ``generate``
        method if it supports them.
        """

        return self.llm.generate(prompt, **kwargs) if hasattr(self.llm, "generate") else self.llm(prompt, **kwargs)
