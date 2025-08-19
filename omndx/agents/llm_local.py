from __future__ import annotations

import os, time, logging, warnings
from typing import Any, List, Mapping, Protocol, runtime_checkable


@runtime_checkable
class LLM(Protocol):
    """Minimal protocol for language model backends."""
    def run(self, prompt: str, **kwargs: Any) -> str: ...


class EchoLLM:
    """Test double that echoes the prompt."""

    def run(self, prompt: str, **_: Any) -> str:
        return prompt

    generate = run
    __call__ = run


class FakeListLLM:
    """Deterministic LLM returning predefined responses."""

    def __init__(self, responses: List[str], mode: str = "cycle") -> None:
        self._responses = list(responses)
        self._mode = mode
        self._last = self._responses[-1] if self._responses else ""

    def run(self, prompt: str, **_: Any) -> str:
        if self._responses:
            out = self._responses.pop(0)
            self._last = out
            return out
        return self._last if self._mode == "cycle" else ""

    generate = run
    __call__ = run


class LangChainLLM:
    """Adapter using LangChain when available with strict config validation."""

    def __init__(self, config: Mapping[str, Any]) -> None:
        cfg = dict(config)
        self._fake: FakeListLLM | None = None
        self._call: Any | None = None
        self._backend = "unknown"
        debug = os.getenv("OMNDX_LLM_DEBUG")

        if "responses" in cfg:
            unknown = set(cfg) - {"responses", "responses_mode"}
            if unknown:
                raise ValueError(f"Unknown config keys: {unknown}")
            mode = cfg.get("responses_mode", "cycle")
            self._fake = FakeListLLM(cfg.get("responses") or [], mode=mode)
            self._backend = "fake"
            if debug:
                logging.getLogger("omndx.llm").info("backend=%s", self._backend)
            return

        unknown = set(cfg) - {"model_name", "endpoint", "api_key", "temperature"}
        if unknown:
            raise ValueError(f"Unknown config keys: {unknown}")

        model_name = cfg.get("model_name", os.getenv("OMNDX_MODEL", "gpt-3.5-turbo"))
        temperature = float(cfg.get("temperature", 0))
        api_key = cfg.get("api_key") or os.getenv("OPENAI_API_KEY")
        endpoint = cfg.get("endpoint")
        if not api_key:
            raise ValueError("api_key required for LangChainLLM")

        call = None
        backend = None
        try:  # prefer modern langchain_openai packaging
            from langchain_openai import ChatOpenAI  # type: ignore

            llm = ChatOpenAI(model_name=model_name, temperature=temperature, api_key=api_key)

            def _call(prompt: str, **kwargs: Any) -> str:
                return llm.predict(prompt, **kwargs)

            call = _call
            backend = "langchain_openai"
        except Exception:
            try:
                from langchain_community.llms import OpenAI as LCOpenAI  # type: ignore

                warnings.warn(
                    "langchain_community.llms.OpenAI is deprecated",
                    DeprecationWarning,
                )
                llm = LCOpenAI(
                    model_name=model_name,
                    temperature=temperature,
                    openai_api_key=api_key,
                )

                def _call(prompt: str, **kwargs: Any) -> str:
                    return llm.predict(prompt, **kwargs)

                call = _call
                backend = "langchain_community"
            except Exception:
                try:
                    import openai  # type: ignore

                    openai.api_key = api_key
                    if endpoint:
                        openai.api_base = endpoint

                    def _call(prompt: str, **kwargs: Any) -> str:
                        resp = openai.ChatCompletion.create(
                            model=model_name,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=temperature,
                            **kwargs,
                        )
                        return resp["choices"][0]["message"]["content"]

                    call = _call
                    backend = "openai"
                except Exception as e:  # pragma: no cover - import error
                    raise RuntimeError("No LLM backend available") from e

        self._call = call
        self._backend = backend or "unknown"
        if debug:
            logging.getLogger("omndx.llm").info("backend=%s", self._backend)

    def run(self, prompt: str, **kwargs: Any) -> str:
        if self._fake is not None:
            return self._fake.run(prompt, **kwargs)
        if self._call is None:
            raise RuntimeError("LLM not configured")
        start = time.perf_counter()
        out = self._call(prompt, **kwargs)
        if os.getenv("OMNDX_LLM_DEBUG"):
            logging.getLogger("omndx.llm").info(
                "backend=%s duration=%.3f", self._backend, time.perf_counter() - start
            )
        return out

    generate = run
    __call__ = run


__all__ = ["LLM", "LangChainLLM", "EchoLLM", "FakeListLLM"]
