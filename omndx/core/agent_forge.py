"""Agent factory and template registry for the OMNDX platform.

TODO:
- Telemetry: trace agent creation events.
- Metrics: report factory performance and failures.
- Security: validate templates from untrusted sources.
- Resiliency: support hot-reload of templates and rollback.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Type

from pydantic import BaseModel, ValidationError

from omndx.runtime.metrics_collector import metrics


@dataclass
class Template:
    """Definition of an agent template held in the registry."""

    agent_cls: Type[Any]
    config_model: Type[BaseModel]
    dependencies: Dict[str, Any] = field(default_factory=dict)


class AgentForge:
    """Factory responsible for constructing and configuring agent instances."""

    def __init__(self) -> None:
        self._registry: Dict[str, Template] = {}

    def register_template(
        self,
        template_id: str,
        agent_cls: Type[Any],
        config_model: Type[BaseModel],
        dependencies: Dict[str, Any] | None = None,
    ) -> None:
        """Register an agent template with optional dependencies."""

        self._registry[template_id] = Template(
            agent_cls=agent_cls,
            config_model=config_model,
            dependencies=dependencies or {},
        )

    def create_agent(self, template_id: str, **overrides: Any) -> Any:
        """Instantiate an agent from a registered template."""

        start = time.perf_counter()
        tags = {"module": "AgentForge", "template_id": template_id}
        metrics.record("reliability", 0, tags | {"event": "attempt"})
        try:
            template = self._registry[template_id]
            config = template.config_model(**overrides)
            agent = template.agent_cls(
                **config.model_dump(),
                **template.dependencies,
            )
        except KeyError as exc:
            metrics.record(
                "reliability", 0, tags | {"error": "TemplateNotFound"}
            )
            metrics.record("effectiveness", 0, tags | {"status": "failed"})
            metrics.record("cost", 0.0, tags)
            raise ValueError(f"Unknown template_id: {template_id}") from exc
        except ValidationError as exc:
            metrics.record(
                "reliability", 0, tags | {"error": "ValidationError"}
            )
            metrics.record("effectiveness", 0, tags | {"status": "failed"})
            metrics.record("cost", 0.0, tags)
            raise
        except Exception as exc:
            metrics.record(
                "reliability", 0, tags | {"error": exc.__class__.__name__}
            )
            metrics.record("effectiveness", 0, tags | {"status": "failed"})
            metrics.record("cost", 0.0, tags)
            raise
        else:
            metrics.record("reliability", 1, tags | {"event": "created"})
            metrics.record("effectiveness", 1, tags | {"status": "success"})
            metrics.record("cost", 0.0, tags)
            return agent
        finally:
            duration = time.perf_counter() - start
            metrics.record("efficiency", duration, tags)


__all__ = ["AgentForge"]

