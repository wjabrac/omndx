from __future__ import annotations

import concurrent.futures as _futures
import os
import random
import time
from dataclasses import dataclass
from typing import Any, ClassVar

from omndx.core.instrumentation import TagLogger
from .llm_local import LLM


class BackendError(RuntimeError):
    """Unified error type for backend failures."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        if cause is not None:
            self.__cause__ = cause


@dataclass
class CoreAgent:
    """Minimal core agent that relies on an injected LLM instance.

    Contracts
    ---------
    * Executes the underlying LLM in a single-thread executor enforcing a hard
      timeout.
    * Retries transient failures with jittered backoff.
    * Truncates returned text at any provided stop token.
    * Normalises backend exceptions to :class:`BackendError` while preserving
      the original exception as ``__cause__``.

    Configuration
    -------------
    Defaults are pulled from class variables or environment variables
    ``OMNDX_AGENT_TIMEOUT``, ``OMNDX_AGENT_MAX_RETRIES`` and
    ``OMNDX_AGENT_BACKOFF_BASE``. Each call to :meth:`run` accepts keyword
    overrides ``timeout``, ``max_retries`` and ``backoff_base``.

    Failure Modes
    -------------
    Raises ``BackendError`` with message ``"timeout"`` or ``"backend error"``.
    """

    llm: LLM
    timeout: float | None = None
    max_retries: int | None = None
    backoff_base: float | None = None

    TIMEOUT: ClassVar[float] = 1.0
    MAX_RETRIES: ClassVar[int] = 2
    BACKOFF_BASE: ClassVar[float] = 0.05

    def __post_init__(self) -> None:  # pragma: no cover - simple setters
        self.timeout = self.TIMEOUT if self.timeout is None else self.timeout
        self.timeout = float(os.getenv("OMNDX_AGENT_TIMEOUT", self.timeout))
        self.max_retries = self.MAX_RETRIES if self.max_retries is None else self.max_retries
        self.max_retries = int(os.getenv("OMNDX_AGENT_MAX_RETRIES", self.max_retries))
        self.backoff_base = self.BACKOFF_BASE if self.backoff_base is None else self.backoff_base
        self.backoff_base = float(os.getenv("OMNDX_AGENT_BACKOFF_BASE", self.backoff_base))

    def run(self, prompt: str, **kwargs: Any) -> str:
        """Return the LLM's response for ``prompt`` with resiliency guards."""

        logger = TagLogger(self.__class__.__name__)
        call = getattr(self.llm, "run", None) or getattr(self.llm, "generate", None) or self.llm
        timeout = float(kwargs.pop("timeout", self.timeout))
        max_retries = int(kwargs.pop("max_retries", self.max_retries))
        backoff_base = float(kwargs.pop("backoff_base", self.backoff_base))

        for attempt in range(max_retries + 1):
            start = time.perf_counter()
            try:
                with _futures.ThreadPoolExecutor(max_workers=1) as executor:
                    result = executor.submit(call, prompt, **kwargs).result(timeout=timeout)
                text = str(result)
                stop_tokens = kwargs.get("stop")
                if stop_tokens:
                    tokens = [stop_tokens] if isinstance(stop_tokens, str) else list(stop_tokens)
                    for token in tokens:
                        pos = text.find(token)
                        if pos != -1:
                            text = text[:pos]
                            break
                elapsed = time.perf_counter() - start
                logger.info("llm_call", tag="success", attempt=attempt, elapsed=elapsed)
                return text
            except _futures.TimeoutError as exc:
                elapsed = time.perf_counter() - start
                logger.error("timeout", tag="timeout", attempt=attempt, elapsed=elapsed)
                raise BackendError("timeout", cause=exc)
            except Exception as exc:  # pragma: no cover - catch-all exercised in tests
                elapsed = time.perf_counter() - start
                logger.error("error", tag=exc.__class__.__name__, attempt=attempt, elapsed=elapsed)
                if attempt == max_retries:
                    raise BackendError("backend error", cause=exc)
                delay = backoff_base * (2 ** attempt) + random.uniform(0, backoff_base)
                time.sleep(delay)


__all__ = ["CoreAgent", "BackendError"]
