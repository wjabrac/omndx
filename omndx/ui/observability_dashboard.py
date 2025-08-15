"""Observability links for quick UI access.

This module exposes a small dataclass containing URLs to common observability
interfaces such as Grafana, Jaeger and RabbitMQ management.  It acts as a simple
plug that can be imported by UI layers to provide easy navigation to these
services when they are deployed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class ObservabilityLinks:
    grafana_url: str = "http://localhost:3000"
    jaeger_url: str = "http://localhost:16686"
    rabbitmq_url: str = "http://localhost:15672"

    def as_dict(self) -> Dict[str, str]:
        return {
            "grafana": self.grafana_url,
            "jaeger": self.jaeger_url,
            "rabbitmq": self.rabbitmq_url,
        }


__all__ = ["ObservabilityLinks"]
