import sys
from pathlib import Path

# Ensure the package root is on the Python path for direct test execution
sys.path.append(str(Path(__file__).resolve().parents[1]))

from omndx.agents.llm_local import EchoLLM, LangChainLLM
from omndx.agents.core_agent import CoreAgent


def test_core_agent_with_echo_llm():
    agent = CoreAgent(EchoLLM())
    assert agent.run("hello") == "hello"


def test_core_agent_with_langchain_fake_llm():
    config = {"model_name": "fake-list", "responses": ["hi there"]}
    llm = LangChainLLM(config)
    agent = CoreAgent(llm)
    assert agent.run("hello") == "hi there"


def test_core_agent_callable_fallback():
    agent = CoreAgent(lambda prompt, **_: prompt.upper())
    assert agent.run("ping") == "PING"
