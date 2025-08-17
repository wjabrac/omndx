import sys
import types

def test_langchain_smoke_import_only(monkeypatch):
    # Force imports to exist; do not perform real calls
    import langchain_openai  # noqa: F401
    from omndx.agents.llm_local import LangChainLLM

    class Dummy:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
        def predict(self, prompt, **_):
            return "ok"

    monkeypatch.setitem(sys.modules, "langchain_openai", types.SimpleNamespace(ChatOpenAI=Dummy))
    llm = LangChainLLM({"model_name": "gpt-4o-mini", "api_key": "k"})
    assert llm.generate("x") == "ok"
