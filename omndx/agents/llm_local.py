"""Local LLM implementations used by agents.

This module defines a very small abstraction for language models and
provides two concrete implementations used throughout the tests:

* :class:`EchoLLM` – a trivial LLM that simply echoes the input.  Useful for
  deterministic unit tests.
* :class:`LangChainLLM` – a wrapper around LangChain's ``LLM`` interface.
  The wrapper supports selecting a model via a configuration dictionary which
  may include the ``model_name``, ``endpoint`` and ``api_key``.  Only a tiny
  subset of the LangChain functionality is required for the tests; the class is
  intentionally lightweight.

The goal of this module isn't to be feature complete but to provide a common
interface for the rest of the code base.  Both implementations expose a single
``generate`` method which returns a string response for a given prompt.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Optional, Dict, Any


class LLM(Protocol):
    """Simple protocol all LLM implementations should follow."""

    def generate(self, prompt: str) -> str:
        """Generate a text response for ``prompt``."""


@dataclass
class EchoLLM:
    """A minimal LLM used purely for testing.

    ``generate`` returns the prompt unchanged which provides deterministic
    behaviour for unit tests.
    """

    def generate(self, prompt: str) -> str:  # pragma: no cover - trivial
        return prompt


class LangChainLLM:
    """Wrap a LangChain ``LLM`` instance.

    Parameters are provided via a configuration dictionary.  The following keys
    are recognised:

    ``model_name``:
        Identifier for the model.  When set to ``"fake-list"`` a
        ``FakeListLLM`` from ``langchain_community`` is used which requires no
        external services and is ideal for tests.  For any other value the
        ``OpenAI`` implementation from ``langchain_community`` is used.
    ``endpoint``:
        Optional API base URL passed to the underlying model (when supported).
    ``api_key``:
        Optional API key for authenticated models.
    Additional keys are forwarded to the LangChain model constructor allowing
    tests to pass ``responses`` for ``FakeListLLM`` for example.
    """

    def __init__(self, config: Dict[str, Any]):
        model_name: str = config.get("model_name", "")
        endpoint: Optional[str] = config.get("endpoint")
        api_key: Optional[str] = config.get("api_key")
        extra: Dict[str, Any] = {k: v for k, v in config.items() if k not in {"model_name", "endpoint", "api_key"}}

        # Lazily import LangChain to avoid importing heavy dependencies when the
        # class is unused (e.g. in simple tests).
        if model_name == "fake-list":
            from langchain_community.llms.fake import FakeListLLM

            self._llm = FakeListLLM(**extra)
        else:
            from langchain_community.llms import OpenAI

            if endpoint:
                extra["openai_api_base"] = endpoint
            if api_key:
                extra["openai_api_key"] = api_key
            if model_name:
                extra["model_name"] = model_name
            self._llm = OpenAI(**extra)

    def generate(self, prompt: str) -> str:
        """Delegate generation to the underlying LangChain model."""

        # ``invoke`` is the stable API in modern LangChain releases and returns
        # a string for standard LLMs.
        return self._llm.invoke(prompt)
