import importlib

import pytest

from omndx import preflight


def test_preflight_requires_key(monkeypatch):
    monkeypatch.setenv("OMNDX_REQUIRE_REAL_BACKEND", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        importlib.reload(preflight).check()


def test_preflight_pass(monkeypatch):
    monkeypatch.setenv("OMNDX_REQUIRE_REAL_BACKEND", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    importlib.reload(preflight).check()


def test_preflight_timeout(monkeypatch):
    monkeypatch.delenv("OMNDX_REQUIRE_REAL_BACKEND", raising=False)
    monkeypatch.setenv("OMNDX_AGENT_TIMEOUT", "100")
    with pytest.raises(RuntimeError):
        importlib.reload(preflight).check()
