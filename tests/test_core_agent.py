from omndx.agents import CoreAgent, BackendError, EchoLLM, FakeListLLM, build_default_agents, AgentLogger
import pytest, time


class GenerateOnlyLLM:
    def generate(self, prompt: str) -> str:  # pragma: no cover - used in tests
        return prompt.upper()


def test_core_agent_callable_and_generate_fallbacks():
    def callable_llm(prompt: str) -> str:
        return prompt[::-1]

    agent_gen = CoreAgent(GenerateOnlyLLM())
    agent_call = CoreAgent(callable_llm)
    assert agent_gen.run("hi") == "HI"
    assert agent_call.run("abc") == "cba"


def test_core_agent_timeout_and_backend_error():
    class SlowLLM:
        def run(self, prompt: str) -> str:
            time.sleep(0.2)
            return prompt

    class FailLLM:
        def run(self, prompt: str) -> str:
            raise ValueError("boom")

    agent_timeout = CoreAgent(SlowLLM(), timeout=0.05, max_retries=0)
    with pytest.raises(TimeoutError):
        agent_timeout.run("x")

    agent_fail = CoreAgent(FailLLM(), max_retries=1)
    with pytest.raises(BackendError) as ei:
        agent_fail.run("x")
    assert isinstance(ei.value.__cause__, ValueError)


def test_core_agent_repeated_calls_no_leak():
    agent = CoreAgent(EchoLLM())
    for _ in range(5):
        assert agent.run("ping") == "ping"


def test_core_agent_stop_tokens():
    agent = CoreAgent(FakeListLLM(["hello STOP extra"]), stop=["STOP"]) 
    assert agent.run("x") == "hello "


def test_logger_info_warning(caplog):
    logger = AgentLogger("test")
    with caplog.at_level("INFO"):
        logger.info("event", {"a": 1})
        logger.warning("warn", {"b": 2})
    assert any("event" in r.message for r in caplog.records)
    assert any("warn" in r.message for r in caplog.records)


def test_factory_no_arg_success():
    agents = build_default_agents()
    out = agents["planner"].plan("test", max_steps=1)
    assert out
