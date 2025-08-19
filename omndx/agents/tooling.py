from __future__ import annotations

from typing import Protocol, Any


class Tool(Protocol):
    name: str
    description: str
    def run(self, **kwargs: Any) -> Any: ...


class RouterAgent:
    def __init__(self, tools: dict[str, Tool]) -> None:
        self.tools = tools

    def route(self, request: str, tool: str | None = None) -> Any:
        if tool is not None and tool in self.tools:
            if tool == "planner":
                return self.tools[tool].run(goal=request)
            if tool == "tagger":
                return self.tools[tool].run(text=request)
            return self.tools[tool].run(request=request)
        r = request.lower()
        if "plan" in r or "steps" in r:
            return self.tools["planner"].run(goal=request)
        if "tag" in r or "tags" in r:
            return self.tools["tagger"].run(text=request)
        return self.tools["recommender"].run(request=request)


__all__ = ["Tool", "RouterAgent"]
