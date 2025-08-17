"""Light‑weight LLM adapter used by agents.

The module exposes a tiny :class:`LLM` protocol and two concrete
implementations:

* :class:`EchoLLM` – deterministic echo used for simple tests.
* :class:`LangChainLLM` – runtime adapter that wraps LangChain style models.

The adapter intentionally keeps the public surface minimal: a single
``generate`` method.  At initialisation the underlying model's preferred call
path (``invoke``, ``predict`` or ``__call__``) is detected and stored so that
``generate`` becomes the stable entry point.

For tests the special ``model_name="fake-list"`` activates a self contained
``FakeListLLM`` which cycles through a list of responses without requiring any
external dependencies.  When ``model_name`` is anything else the adapter tries
``langchain_openai.ChatOpenAI`` first and falls back to
``langchain_community.llms.OpenAI``.  Test only configuration keys such as
``responses`` are stripped from production backends to avoid accidental leaks.

All configuration keys are validated.  Unknown keys for production models
raise :class:`ValueError` with the offending key names.  The adapter emits
structured debug logs describing the backend selection and call timing when the
``OMNDX_LLM_DEBUG`` environment variable is set.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

logger = logging.getLogger("omndx.llm")


class LLM(Protocol):
    """Common protocol all LLM implementations follow."""

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Return a text response for ``prompt``."""


@dataclass
class EchoLLM:
    """A trivial LLM that simply echoes the prompt back."""

    def generate(self, prompt: str, **_: Any) -> str:  # pragma: no cover - trivial
        return prompt


class FakeListLLM:
    """Minimal stand‑alone fake LLM used for tests.

    ``responses`` is an iterable of predetermined outputs.  The list is cycled
    and once exhausted the last response is repeated.
    """

    def __init__(self, responses: Optional[List[str]] = None) -> None:
        self._responses = responses or []
        self._index = 0

    def invoke(self, _: str, **__: Any) -> str:
        if not self._responses:
            return ""
        if self._index >= len(self._responses):
            return self._responses[-1]
        resp = self._responses[self._index]
        self._index += 1
        return resp


class LangChainLLM:
    """Adapter over LangChain compatible backends."""

    _TEST_KEYS = {"responses"}
    _PROD_KEYS = {"model_name", "endpoint", "api_key"}

    def __init__(self, config: Dict[str, Any]):
        self.config = dict(config)
        model_name = self.config.get("model_name", "")
        endpoint = self.config.get("endpoint")
        api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")

        allowed = self._PROD_KEYS | (self._TEST_KEYS if model_name == "fake-list" else set())
        unknown = set(self.config) - allowed
        if unknown and model_name != "fake-list":
            raise ValueError(f"Unknown config keys: {sorted(unknown)}")

        if model_name == "fake-list":
            responses = self.config.get("responses")
            self.backend = "fake-list"
            self._llm: Any = FakeListLLM(responses)
        else:
            extra = {k: v for k, v in self.config.items() if k not in self._PROD_KEYS | self._TEST_KEYS}
            if not api_key:
                raise ValueError("api_key required for production backends")
            try:
                from langchain_openai import ChatOpenAI

                self.backend = "langchain_openai.ChatOpenAI"
                self._llm = ChatOpenAI(model=model_name, base_url=endpoint, api_key=api_key, **extra)
            except Exception:  # pragma: no cover - exercised via tests
                from langchain_community.llms import OpenAI

                self.backend = "langchain_community.llms.OpenAI"
                if endpoint:
                    extra["openai_api_base"] = endpoint
                extra["openai_api_key"] = api_key
                if model_name:
                    extra["model_name"] = model_name
                self._llm = OpenAI(**extra)
                logger.warning(
                    "OpenAI backend is deprecated and will be removed in a future release", stacklevel=2
                )

        if hasattr(self._llm, "invoke"):
            self._call = self._llm.invoke
        elif hasattr(self._llm, "predict"):
            self._call = self._llm.predict
        else:
            self._call = self._llm

        if os.getenv("OMNDX_LLM_DEBUG"):
            redacted = endpoint[:5] + "…" if endpoint else None
            logger.debug("backend=%s model=%s endpoint=%s", self.backend, model_name, redacted)

    def generate(self, prompt: str, **kwargs: Any) -> str:
        start = time.perf_counter()
        result = self._call(prompt, **kwargs)
        duration = time.perf_counter() - start
        if os.getenv("OMNDX_LLM_DEBUG"):
            logger.debug("call backend=%s duration=%.3f", self.backend, duration)
        return str(result)
