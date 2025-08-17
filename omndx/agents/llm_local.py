"""Light-weight LLM adapter used by agents.

Public surface: a single LLM protocol with generate(prompt, **kwargs) -> str,
plus two concrete implementations:
- EchoLLM: deterministic echo for tests
- LangChainLLM: adapter over LangChain-compatible backends

Special case: model_name="fake-list" selects an internal FakeListLLM that
cycles through predefined responses. No external dependencies are required.
Production backends require an API key; unknown config keys are rejected.
Lazy import LangChain only on the production path.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

logger = logging.getLogger("omndx.llm")

__all__ = ["LLM", "EchoLLM", "FakeListLLM", "LangChainLLM"]


class LLM(Protocol):
    """Common protocol all LLM implementations follow."""

    def generate(self, prompt: str, **kwargs: Any) -> str: ...


@dataclass
class EchoLLM:
    """A trivial LLM that simply echoes the prompt back."""

    def generate(self, prompt: str, **_: Any) -> str:  # pragma: no cover
        return prompt


class FakeListLLM:
    """Minimal stand-alone fake LLM used for tests.

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

    # Provide a generate method to match our protocol
    def generate(self, prompt: str, **__: Any) -> str:  # pragma: no cover
        return self.invoke(prompt)


class LangChainLLM:
    """Adapter over LangChain-compatible backends."""

    _TEST_KEYS = {"responses"}
    _PROD_KEYS = {"model_name", "endpoint", "api_key"}

    def __init__(self, config: Dict[str, Any]):
        self.config = dict(config)
        model_name = str(self.config.get("model_name", ""))
        endpoint = self.config.get("endpoint")
        api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
        self._call: Any

        allowed = self._PROD_KEYS | (self._TEST_KEYS if model_name == "fake-list" else set())
        unknown = set(self.config) - allowed
        if unknown and model_name != "fake-list":
            raise ValueError(f"Unknown config keys: {sorted(unknown)}")

        if model_name == "fake-list":
            self.backend = "fake-list"
            responses = self.config.get("responses")
            self._llm = FakeListLLM(responses=responses)
            self._call = self._llm.generate
            if os.getenv("OMNDX_LLM_DEBUG"):
                logger.debug("backend=%s", self.backend)
            return

        # Production backends
        if not api_key:
            raise ValueError("api_key required for production backends")
        extra = {k: v for k, v in self.config.items() if k not in self._PROD_KEYS | self._TEST_KEYS}

        try:
            from langchain_openai import ChatOpenAI
            self.backend = "langchain_openai.ChatOpenAI"
            self._llm = ChatOpenAI(model=model_name, base_url=endpoint, api_key=api_key, **extra)
            call = getattr(self._llm, "invoke", None) or getattr(self._llm, "predict", None) or self._llm
            self._call = call
        except Exception:
            from langchain_community.llms import OpenAI
            self.backend = "langchain_community.llms.OpenAI"
            if endpoint:
                extra["openai_api_base"] = endpoint  # pragma: no cover - URL rarely needed in tests
            extra["openai_api_key"] = api_key
            if model_name:
                extra["model_name"] = model_name
            self._llm = OpenAI(**extra)
            self._call = getattr(self._llm, "invoke", None) or getattr(self._llm, "predict", None) or self._llm
            logger.warning("OpenAI backend is deprecated and will be removed in a future release", stacklevel=2)

        if os.getenv("OMNDX_LLM_DEBUG"):
            redacted = (endpoint[:5] + "…") if endpoint else None
            logger.debug("backend=%s model=%s endpoint=%s", self.backend, model_name, redacted)

    def generate(self, prompt: str, **kwargs: Any) -> str:
        start = time.perf_counter()
        result = self._call(prompt, **kwargs)
        duration = time.perf_counter() - start
        if os.getenv("OMNDX_LLM_DEBUG"):
            logger.debug("call backend=%s duration=%.3f", self.backend, duration)
        return str(result)

