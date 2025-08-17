"""Tests for :mod:`omndx.core.agent_forge`."""

from pydantic import BaseModel, ValidationError
import pytest

from omndx.core.agent_forge import AgentForge
from omndx.agents.agent_template import Agent


class _Config(BaseModel):
    name: str = "default"


def test_create_agent_success() -> None:
    forge = AgentForge()
    forge.register_template("tmpl", Agent, _Config)
    agent = forge.create_agent("tmpl", name="alpha")
    assert isinstance(agent, Agent)
    assert agent.name == "alpha"


def test_create_agent_unknown_template() -> None:
    forge = AgentForge()
    with pytest.raises(ValueError):
        forge.create_agent("missing")


def test_create_agent_validation_error() -> None:
    class NoDefault(BaseModel):
        name: str

    forge = AgentForge()
    forge.register_template("tmpl", Agent, NoDefault)
    with pytest.raises(ValidationError):
        forge.create_agent("tmpl")

