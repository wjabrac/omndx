"""Core agent abstraction.

The :class:`CoreAgent` is intentionally lightweight.  It accepts any object
implementing the :class:`~omndx.agents.llm_local.LLM` protocol and delegates
text generation to it.  The purpose of the class is to provide a single place
where different LLM implementations can be plugged in, allowing tests to use a
simple echo model or a LangChain powered one.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

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

        if hasattr(self.llm, "generate"):
            return str(self.llm.generate(prompt, **kwargs))
        # Fallback to callable models that lack ``generate``
        return str(cast(Any, self.llm)(prompt, **kwargs))
