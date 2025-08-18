import time

import pytest

from omndx.agents.llm_local import EchoLLM, LangChainLLM
from omndx.agents.core_agent import BackendError, CoreAgent


def test_core_agent_with_echo_llm():
    agent = CoreAgent(EchoLLM())
    assert agent.run("hello") == "hello"


def test_core_agent_with_langchain_fake_llm():
    config = {"model_name": "fake-list", "responses": ["hi there"]}
    agent = CoreAgent(LangChainLLM(config, require_real_backend=False))
    assert agent.run("hello") == "hi there"


def test_core_agent_callable_fallback():
    agent = CoreAgent(lambda prompt, **_: prompt.upper())
    assert agent.run("ping") == "PING"


def test_core_agent_run_method_precedence():
    class Dummy:
        def run(self, prompt, **_):
            return "run"

        def generate(self, prompt, **_):  # pragma: no cover
            return "generate"

    agent = CoreAgent(Dummy())
    assert agent.run("x") == "run"


def test_core_agent_timeout_override():
    def slow(prompt, **_):
        time.sleep(0.2)
        return "ok"

    agent = CoreAgent(slow)
    with pytest.raises(BackendError):
        agent.run("x", timeout=0.05)


def test_core_agent_retry_success():
    calls = {"n": 0}

    def flaky(prompt, **_):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("fail")
        return "ok"

    agent = CoreAgent(flaky, max_retries=1, backoff_base=0.0)
    assert agent.run("hi") == "ok"


def test_core_agent_retry_exhaustion():
    def boom(prompt, **_):
        raise RuntimeError("boom")

    agent = CoreAgent(boom, max_retries=1, backoff_base=0.0)
    with pytest.raises(BackendError):
        agent.run("x")


def test_core_agent_stop_token_truncation_str():
    agent = CoreAgent(EchoLLM())
    assert agent.run("hello END world", stop="END") == "hello "


def test_core_agent_stop_token_truncation_list():
    agent = CoreAgent(EchoLLM())
    assert agent.run("hello END1 world END2", stop=["END1", "END2"]) == "hello "


def test_core_agent_error_wrapping():
    def boom(prompt, **_):
        raise ValueError("x")

    agent = CoreAgent(boom, max_retries=0)
    with pytest.raises(BackendError) as exc:
        agent.run("y")
    assert isinstance(exc.value.__cause__, ValueError)
