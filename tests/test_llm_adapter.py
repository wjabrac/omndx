import sys
import types
import pytest
from omndx.agents.llm_local import LangChainLLM


def test_fake_list_cycles(monkeypatch):
    monkeypatch.setenv("OMNDX_LLM_DEBUG", "1")
    llm = LangChainLLM({"model_name": "fake-list", "responses": ["a", "b"]})
    assert llm.generate("x") == "a"
    assert llm.generate("x") == "b"
    assert llm.generate("x") == "b"


def test_fake_list_empty():
    llm = LangChainLLM({"model_name": "fake-list"})
    assert llm.generate("x") == ""


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


def test_missing_api_key():
    with pytest.raises(ValueError):
        LangChainLLM({"model_name": "gpt"})
