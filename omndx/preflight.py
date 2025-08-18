"""Production safety checks."""

from __future__ import annotations

import os

from omndx.agents.core_agent import CoreAgent


def check() -> None:
    """Raise ``RuntimeError`` if configuration is unsafe for production."""
    require_real = os.getenv("OMNDX_REQUIRE_REAL_BACKEND") == "1"
    api_key = os.getenv("OPENAI_API_KEY")
    timeout = float(os.getenv("OMNDX_AGENT_TIMEOUT", CoreAgent.TIMEOUT))
    if require_real and not api_key:
        raise RuntimeError("[preflight] require_real_backend set but OPENAI_API_KEY missing")
    if timeout <= 0 or timeout > 60:
        raise RuntimeError(f"[preflight] unreasonable timeout {timeout}")
