import sys, types
import pytest

from omndx.agents.llm_local import LangChainLLM


def test_fake_list_cycle_mode():
    llm = LangChainLLM({"responses": ["a", "b"]})
    assert llm.run("x") == "a"
    assert llm.run("x") == "b"
    assert llm.run("x") == "b"


def test_fake_list_pop_mode():
    llm = LangChainLLM({"responses": ["a", "b"], "responses_mode": "pop"})
    assert llm.run("x") == "a"
    assert llm.run("x") == "b"
    assert llm.run("x") == ""


def test_fake_list_empty_responses():
    llm = LangChainLLM({"responses": []})
    assert llm.run("x") == ""


def test_prefers_chatopenai(monkeypatch):
    class StubChatOpenAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def predict(self, prompt: str) -> str:
            return "lc" + prompt

    mod = types.SimpleNamespace(ChatOpenAI=StubChatOpenAI)
    monkeypatch.setitem(sys.modules, "langchain_openai", mod)
    llm = LangChainLLM({"model_name": "foo", "api_key": "key"})
    assert llm.run("hi") == "lchi"


def test_openai_deprecated_fallback(monkeypatch):
    class LCOpenAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def predict(self, prompt: str, **kwargs) -> str:
            return "lc" + prompt

    mod_llms = types.SimpleNamespace(OpenAI=LCOpenAI)
    mod_comm = types.SimpleNamespace(llms=mod_llms)
    monkeypatch.delitem(sys.modules, "langchain_openai", raising=False)
    monkeypatch.setitem(sys.modules, "langchain_community", mod_comm)
    monkeypatch.setitem(sys.modules, "langchain_community.llms", mod_llms)
    with pytest.warns(DeprecationWarning):
        llm = LangChainLLM({"model_name": "foo", "api_key": "key"})
    assert llm.run("hi") == "lchi"


def test_openai_fallback(monkeypatch):
    class ChatCompletion:
        @staticmethod
        def create(**kwargs):
            return {"choices": [{"message": {"content": "oa"}}]}

    mod_openai = types.SimpleNamespace(ChatCompletion=ChatCompletion, api_key=None)
    monkeypatch.delitem(sys.modules, "langchain_openai", raising=False)
    monkeypatch.delitem(sys.modules, "langchain_community", raising=False)
    monkeypatch.delitem(sys.modules, "langchain_community.llms", raising=False)
    monkeypatch.setitem(sys.modules, "openai", mod_openai)
    llm = LangChainLLM({"model_name": "foo", "api_key": "k"})
    assert llm.run("x") == "oa"


def test_unknown_key_validation():
    with pytest.raises(ValueError):
        LangChainLLM({"unknown": 1})


def test_missing_api_key_raises():
    with pytest.raises(ValueError):
        LangChainLLM({"model_name": "foo"})
