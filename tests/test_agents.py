from omndx.agents import (
    LangChainLLM,
    PlannerAgent,
    TaggerAgent,
    RecommenderAgent,
    RouterAgent,
    build_default_agents,
)
from omndx.storage.chat_memory import ChatMemory
import os
import tempfile


def fake_llm(responses):
    return LangChainLLM({"responses": list(responses)})


def test_planner_agent_parses_steps():
    agent = PlannerAgent(fake_llm(["1. step1\n2. step2\n\n"]))
    assert agent.plan("goal") == ["step1", "step2"]


def test_tagger_agent_splits_tags_and_dedupes():
    agent = TaggerAgent(fake_llm(["tag1, tag2; tag1"]))
    assert agent.tag("text") == ["tag1", "tag2"]


def test_recommender_agent_returns_lines():
    agent = RecommenderAgent(fake_llm(["- a\n- b\n"]))
    assert agent.recommend("req") == ["a", "b"]


def test_router_routes_to_correct_tool():
    llm = fake_llm(["1. step\n", "tag1", "- item1\n"])
    agents = build_default_agents(llm)
    router = RouterAgent(agents)
    assert router.route("plan something") == ["step"]
    assert router.route("please tag this") == ["tag1"]
    assert router.route("anything else") == ["item1"]


def test_router_explicit_override():
    llm = fake_llm(["1. step\n", "tag1"])
    agents = build_default_agents(llm)
    router = RouterAgent(agents)
    assert router.route("ignore", tool="planner") == ["step"]
    assert router.route("ignore", tool="tagger") == ["tag1"]


def test_planner_agent_stores_memory():
    with tempfile.TemporaryDirectory() as tmp:
        mem = ChatMemory(db_path=os.path.join(tmp, "mem.sqlite"))
        agent = PlannerAgent(fake_llm(["1. x\n\n"]), memory=mem)
        agent.plan("goal", session_id="s1")
        conv = mem.get_conversation("s1")
        assert len(conv) == 2
        assert conv[0]["role"] == "user"
        assert conv[1]["role"] == "assistant"
