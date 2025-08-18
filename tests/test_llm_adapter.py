import sys
import types

import pytest

from omndx.agents.llm_local import LangChainLLM


def test_fake_list_cycles(monkeypatch):
    monkeypatch.setenv("OMNDX_LLM_DEBUG", "1")
    monkeypatch.delenv("OMNDX_REQUIRE_REAL_BACKEND", raising=False)
    llm = LangChainLLM({"model_name": "fake-list", "responses": ["a", "b"]})
    assert llm.generate("x") == "a"
    assert llm.generate("x") == "b"
    assert llm.generate("x") == "b"


def test_fake_list_default_response():
    llm = LangChainLLM({"model_name": "fake-list"}, require_real_backend=False)
    assert llm.generate("x") == "fake-response"


def test_fake_list_pop_mode():
    llm = LangChainLLM({"model_name": "fake-list", "responses": ["a", "b"], "responses_mode": "pop"}, require_real_backend=False)
    assert llm.generate("x") == "a"
    assert llm.generate("x") == "b"
    assert llm.generate("x") == ""


def test_responses_mode_invalid():
    with pytest.raises(ValueError):
        LangChainLLM({"model_name": "fake-list", "responses_mode": "bad"})


def test_predict_call_path(monkeypatch):
    class Dummy:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
        def predict(self, prompt, **_):
            return "ok"
    monkeypatch.setitem(sys.modules, "langchain_openai", types.SimpleNamespace(ChatOpenAI=Dummy))
    llm = LangChainLLM({"model_name": "gpt", "api_key": "k"})
    assert llm.generate("x") == "ok"
    assert "responses" not in llm.config


def test_temperature_passthrough(monkeypatch):
    captured = {}

    class Dummy:
        def __init__(self, **kwargs):
            captured.update(kwargs)
        def predict(self, prompt, **_):
            return "ok"

    monkeypatch.setitem(sys.modules, "langchain_openai", types.SimpleNamespace(ChatOpenAI=Dummy))
    LangChainLLM({"model_name": "gpt", "api_key": "k", "temperature": 0.3})
    assert captured["temperature"] == 0.3


def test_openai_fallback_filters(monkeypatch, caplog):
    caplog.set_level("WARNING")
    class Dummy:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
        def __call__(self, prompt, **_):
            return "pong"
    monkeypatch.setitem(sys.modules, "langchain_openai", None)
    llms_module = types.SimpleNamespace(OpenAI=Dummy)
    monkeypatch.setitem(sys.modules, "langchain_community.llms", llms_module)
    monkeypatch.setenv("OMNDX_LLM_DEBUG", "1")
    llm = LangChainLLM({"model_name": "gpt", "api_key": "k"})
    assert llm.generate("y") == "pong"
    assert "responses" not in llm._llm.kwargs
    assert any("deprecated" in r.message for r in caplog.records)


def test_openai_rejects_test_keys(monkeypatch):
    monkeypatch.setitem(sys.modules, "langchain_openai", None)
    class Dummy:
        def __init__(self, **kwargs):
            pass
    monkeypatch.setitem(sys.modules, "langchain_community.llms", types.SimpleNamespace(OpenAI=Dummy))
    with pytest.raises(ValueError):
        LangChainLLM({"model_name": "gpt", "api_key": "k", "responses": ["x"]})


def test_unknown_key_error():
    with pytest.raises(ValueError):
        LangChainLLM({"model_name": "gpt", "api_key": "k", "foo": 1})


def test_unknown_key_error_fake():
    with pytest.raises(ValueError):
        LangChainLLM({"model_name": "fake-list", "foo": 1})


def test_missing_api_key_requires_real_backend_when_model_specified(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        LangChainLLM({"model_name": "gpt"})


def test_missing_api_key_requires_real_backend_flag(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        LangChainLLM({}, require_real_backend=True)


def test_require_real_backend_blocks_fake():
    with pytest.raises(ValueError):
        LangChainLLM({"model_name": "fake-list"}, require_real_backend=True)


def test_default_fake_warns(monkeypatch, caplog):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OMNDX_REQUIRE_REAL_BACKEND", raising=False)
    caplog.set_level("WARNING")
    llm = LangChainLLM({"endpoint": "https://api.example.com"})
    assert llm.generate("x") == "fake-response"
    assert any("defaulting to fake backend" in r.message for r in caplog.records)


def test_missing_api_key_defaults_to_fake(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OMNDX_REQUIRE_REAL_BACKEND", raising=False)
    llm = LangChainLLM({})
    assert llm.generate("x") == "fake-response"


def test_temperature_passthrough_openai(monkeypatch):
    captured = {}

    class Dummy:
        def __init__(self, **kwargs):
            captured.update(kwargs)
        def __call__(self, prompt, **_):
            return "ok"

    monkeypatch.setitem(sys.modules, "langchain_openai", None)
    llms_module = types.SimpleNamespace(OpenAI=Dummy)
    monkeypatch.setitem(sys.modules, "langchain_community.llms", llms_module)
    LangChainLLM({"model_name": "gpt", "api_key": "k", "temperature": 0.2})
    assert captured["temperature"] == 0.2
