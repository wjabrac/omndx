# Agent Forge

`AgentForge` is a small factory responsible for constructing agents from
registered templates.  Each template defines the target agent class, a
`pydantic` configuration model and optional dependencies to be injected at
construction time.

## Registering a template

```python
from pydantic import BaseModel
from omndx.core.agent_forge import AgentForge
from omndx.agents.agent_template import Agent

class Config(BaseModel):
    name: str = "demo"

forge = AgentForge()
forge.register_template("demo", Agent, Config)
```

## Creating an agent

```python
agent = forge.create_agent("demo", name="alpha")
```

Configuration overrides are validated by `pydantic` and injected into the
agent's constructor along with any registered dependencies.

