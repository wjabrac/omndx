from omndx.agents.tagger_agent import TaggerAgent
from omndx.agents.recommender_agent import RecommenderAgent
from omndx.agents.repair_agent import RepairAgent


def test_tagger_agent() -> None:
    agent = TaggerAgent()
    assert agent.run("Hello world") == ["hello", "world"]


def test_recommender_agent() -> None:
    agent = RecommenderAgent()
    recs = agent.run("python")
    assert "python" in recs[0]


def test_repair_agent() -> None:
    agent = RepairAgent()
    assert agent.run("Too   many   spaces") == "Too many spaces"
