from __future__ import annotations

import random
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass
from typing import Optional, Sequence, Any, Callable

from .llm_local import LLM
from .agent_logger import AgentLogger


class BackendError(RuntimeError):
    """Raised when the LLM backend fails."""


@dataclass
class CoreAgent:
    llm: LLM | Any
    max_retries: int = 2
    retry_backoff: float = 0.6
    stop: Optional[Sequence[str]] = None
    timeout: float = 10.0
    logger: Optional[AgentLogger] = None

    def _get_caller(self) -> Callable[[str], str]:
        if hasattr(self.llm, "run"):
            return getattr(self.llm, "run")
        if hasattr(self.llm, "generate"):
            return getattr(self.llm, "generate")
        if callable(self.llm):
            return self.llm  # type: ignore[return-value]
        raise TypeError("LLM backend must implement run, generate or be callable")

    def run(self, prompt: str, **kwargs: Any) -> str:
        caller = self._get_caller()
        attempt = 0
        last_err: Optional[Exception] = None
        while attempt <= self.max_retries:
            start = time.perf_counter()
            try:
                with ThreadPoolExecutor(max_workers=1) as ex:
                    future = ex.submit(caller, prompt, **kwargs)
                    out = future.result(timeout=self.timeout)
                duration = time.perf_counter() - start
                if self.stop:
                    for token in self.stop:
                        if token in out:
                            out = out.split(token, 1)[0]
                            break
                if self.logger:
                    self.logger.debug(
                        "core_agent.run.ok", {"attempt": attempt, "duration": duration}
                    )
                return out
            except FutureTimeout:
                duration = time.perf_counter() - start
                last_err = TimeoutError(f"LLM call exceeded timeout {self.timeout}s")
                if self.logger:
                    self.logger.error(
                        "core_agent.run.timeout",
                        {"attempt": attempt, "duration": duration},
                    )
            except Exception as e:
                duration = time.perf_counter() - start
                last_err = e
                if self.logger:
                    self.logger.error(
                        "core_agent.run.error",
                        {"attempt": attempt, "error": str(e), "duration": duration},
                    )
            if attempt == self.max_retries:
                break
            time.sleep(self.retry_backoff * (1 + random.random()))
            attempt += 1
        if isinstance(last_err, TimeoutError):
            raise last_err
        raise BackendError("LLM call failed after retries") from last_err


__all__ = ["CoreAgent", "BackendError"]
