"""Factory for loading and instantiating agents based on configuration."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Dict, Mapping, MutableMapping


@dataclass
class AgentSpec:
    """Specification for constructing an agent.

    Parameters
    ----------
    path:
        Dotted module path to the agent class (``"package.module.Class"``).
        Alternatively a class object can be provided directly via ``cls``.
    params:
        Keyword arguments passed to the agent constructor.
    cls:
        Direct reference to the class object.  Takes precedence over ``path``.
    """

    path: str | None = None
    params: Mapping[str, Any] | None = None
    cls: type | None = None


class AgentForge:
    """Factory responsible for creating agent instances.

    The forge consumes a mapping of agent names to :class:`AgentSpec`
    definitions.  Agents are created lazily upon first request and cached for
    subsequent retrieval.
    """

    def __init__(self, config: Mapping[str, Mapping[str, Any]]) -> None:
        self._config: Dict[str, AgentSpec] = {
            name: AgentSpec(**spec) for name, spec in config.items()
        }
        self._instances: MutableMapping[str, Any] = {}

    # ------------------------------------------------------------------
    def _load_class(self, spec: AgentSpec) -> type:
        if spec.cls is not None:
            return spec.cls
        if spec.path is None:
            raise ValueError("AgentSpec requires either 'cls' or 'path'")
        module_path, class_name = spec.path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    # ------------------------------------------------------------------
    def get_agent(self, name: str) -> Any:
        """Return an instance of the agent identified by *name*."""

        if name not in self._instances:
            spec = self._config.get(name)
            if spec is None:
                raise KeyError(f"Unknown agent '{name}'")
            cls = self._load_class(spec)
            params = dict(spec.params or {})
            self._instances[name] = cls(**params)
        return self._instances[name]


__all__ = ["AgentForge", "AgentSpec"]
