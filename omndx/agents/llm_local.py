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

    Parameters
    ----------
    responses:
        Iterable of predetermined outputs. If omitted, a deterministic placeholder
        response is used.
    mode:
        ``"cycle"`` (default) cycles through the list and repeats the last
        response once exhausted. ``"pop"`` removes responses from the list and
        returns an empty string when none remain.
    """

    def __init__(self, responses: Optional[List[str]] = None, mode: str = "cycle") -> None:
        self._responses = list(responses or [])
        self._index = 0
        self._mode = mode

    def invoke(self, _: str, **__: Any) -> str:
        if not self._responses:
            return ""
        if self._mode == "pop":
            return self._responses.pop(0) if self._responses else ""
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

    _TEST_KEYS = {"responses", "responses_mode"}
    _PROD_KEYS = {"model_name", "endpoint", "api_key", "temperature"}

    def __init__(self, config: Dict[str, Any], *, require_real_backend: bool | None = None):
        self.config = dict(config)
        model_name = str(self.config.get("model_name", ""))
        endpoint = self.config.get("endpoint")
        api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if require_real_backend is None:
            require_real_backend = os.getenv("OMNDX_REQUIRE_REAL_BACKEND") == "1"
        self._call: Any

        allowed = self._PROD_KEYS | (self._TEST_KEYS if model_name == "fake-list" else set())
        unknown = set(self.config) - allowed
        if unknown and model_name != "fake-list":
            raise ValueError(f"Unknown config keys: {sorted(unknown)}")

        if require_real_backend and (model_name == "fake-list" or not api_key):
            raise ValueError("[LangChainLLM] real backend required; set OPENAI_API_KEY")

        if model_name == "fake-list" or (not model_name and not api_key):
            allowed = {"model_name", "endpoint", "temperature", "responses", "responses_mode"}
            unknown = set(self.config) - allowed
            if unknown:
                raise ValueError(f"Unknown config keys: {sorted(unknown)}")
            responses = self.config.get("responses") or ["fake-response"]
            mode = str(self.config.get("responses_mode", "cycle"))
            if mode not in {"cycle", "pop"}:
                raise ValueError("responses_mode must be 'cycle' or 'pop'")
            self.backend = "fake-list"
            self._llm = FakeListLLM(responses=responses, mode=mode)
            self._call = self._llm.generate
            safe_ep = (endpoint[:5] + "...") if endpoint else None
            logger.warning(
                "[LangChainLLM] defaulting to fake backend model=%s endpoint=%s hint=set OPENAI_API_KEY",
                model_name or "None",
                safe_ep,
            )
            return

        if not api_key:
            raise ValueError("api_key required for production backends")
        extra = {k: v for k, v in self.config.items() if k not in {"model_name", "endpoint", "api_key"}}

        try:
            from langchain_openai import ChatOpenAI  # type: ignore[import-not-found, unused-ignore]
            self.backend = "langchain_openai.ChatOpenAI"
            self._llm = ChatOpenAI(model=model_name, base_url=endpoint, api_key=api_key, **extra)
            call = getattr(self._llm, "invoke", None) or getattr(self._llm, "predict", None) or self._llm
            self._call = call
        except Exception:
            from langchain_community.llms import OpenAI  # type: ignore[import-not-found, unused-ignore]
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
            safe_ep = (endpoint[:5] + "...") if endpoint else None
            logger.debug("backend=%s model=%s endpoint=%s", self.backend, model_name, safe_ep)

    def generate(self, prompt: str, **kwargs: Any) -> str:
        start = time.perf_counter()
        result = self._call(prompt, **kwargs)
        duration = time.perf_counter() - start
        if os.getenv("OMNDX_LLM_DEBUG"):
            logger.debug("call backend=%s duration=%.3f", self.backend, duration)
        return str(result)

